"""
FedMDL Flower server — federated version of MaxSynth / noisy-MDL. Mirrors
engines/collaboration/server.py's structure and bootstrap closely; see
engines/mdl_federation/strategy/fedmdl.py for how the actual search loop
differs from FedPopper's.

The server only ever reads the bias.pl of --dataset — never bk.pl/exs.pl —
since candidate generation is purely ASP/bias-driven (see
popper_mdl.generate.Generator) and all example testing happens on the
clients, against their own local partitions. This mirrors FedPopper's own
server, which similarly builds its Settings with ex_file=None, bk_file=None.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
POPPER_MDL_PATH = os.path.join(PROJECT_ROOT, "symbolic", "Popper-v3")

if POPPER_MDL_PATH not in sys.path:
    sys.path.insert(0, POPPER_MDL_PATH)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import flwr as fl
from flwr.server.server import init_defaults
from flwr.server.superlink.fleet.grpc_bidi.grpc_server import start_grpc_server
from flwr.supercore.address import parse_address
from flwr.common.logger import log
from logging import DEBUG, INFO

from popper_mdl.util import Settings, Stats, load_kbpath

from engines.mdl_federation.strategy.fedmdl import FedMDL, EarlyStopSignal
from engines.mdl_federation.rule_codec import rule_to_text


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the FedMDL Flower server.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to the server dataset (only bias.pl is read)")
    parser.add_argument("--clients", type=int, required=True, help="Number of federated clients expected")
    parser.add_argument("--timeout", type=float, default=600.0, help="Seconds the federated search is allowed to run")
    parser.add_argument("--timing-mode", type=str, choices=["wall", "cpu"], default="wall")
    parser.add_argument(
        "--combine-mode",
        type=str,
        choices=["indices", "signatures"],
        default="indices",
        help=(
            "indices: clients report which of their examples a rule covers and the "
            "server combines during the search (MaxSynth encoding); "
            "signatures: clients report only counts and one signature table at the end."
        ),
    )
    parser.add_argument("--address", type=str, default="0.0.0.0:8080")
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument(
        "--rounds",
        type=int,
        default=10_000_000,
        help="Internal safety cap on Flower rounds — see EarlyStopSignal.",
    )
    return parser.parse_args()


def resolve_dataset_path(dataset_argument: str) -> str:
    dataset_path = (
        dataset_argument
        if os.path.isabs(dataset_argument)
        else os.path.join(PROJECT_ROOT, dataset_argument)
    )
    dataset_path = os.path.abspath(dataset_path)
    if not os.path.isdir(dataset_path):
        raise FileNotFoundError(f"Server dataset directory not found: {dataset_path}")
    return dataset_path


def save_server_result(output_directory: Path, strategy: FedMDL) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)

    solution = None
    if strategy.solution_found and strategy.solution_program:
        solution = "\n".join(rule_to_text(rule) for rule in strategy.solution_program)

    tp = fn = tn = fp = 0
    size = 0
    if strategy.solution_score:
        tp, fn, tn, fp, size = strategy.solution_score

    total_time = strategy.timer() - strategy.global_start
    federation_ratio = strategy.t_federation / total_time if total_time > 0 else 0.0

    result = {
        "solution": solution,
        "solution_found": bool(strategy.solution_found),
        "total_time": float(total_time),
        "startup_time": float(strategy.startup_time or 0.0),
        "learning_time": float(strategy.learning_time or 0.0),
        "popper_time": float(strategy.t_core),
        "federation_time": float(strategy.t_federation),
        "federation_ratio": float(federation_ratio),
        "number_of_rounds": int(strategy.last_round),
        "number_of_programs": int(strategy.total_candidates_tested),
        "final_score": float(tp + tn),
        "tp": int(tp),
        "fn": int(fn),
        "tn": int(tn),
        "fp": int(fp),
        "accuracy": (tp + tn) / (tp + fn + tn + fp) if (tp + fn + tn + fp) else 0.0,
        "precision": tp / (tp + fp) if (tp + fp) else 0.0,
        "recall": tp / (tp + fn) if (tp + fn) else 0.0,
        "pool_size": int(strategy.pool_size),
        "program_size": int(size),
        "mdl_cost": int(size + fn + fp) if strategy.solution_found else None,
        "noisy": True,
    }

    result_path = output_directory / "server_result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    hypothesis_log_path = output_directory / "hypothesis_log.json"
    hypothesis_log_path.write_text(json.dumps(strategy.hypothesis_log, indent=2), encoding="utf-8")

    print(f"[FedMDL Server] Result saved to: {result_path}", flush=True)


def main() -> None:
    args = parse_arguments()
    output_directory = Path(args.output_dir).resolve()

    if args.clients < 1:
        raise ValueError("The number of clients must be at least 1.")

    dataset_path = resolve_dataset_path(args.dataset)

    print("========== FEDMDL SERVER ==========", flush=True)
    print(f"Dataset           : {dataset_path}", flush=True)
    print(f"Number of clients : {args.clients}", flush=True)
    print(f"Server address    : {args.address}", flush=True)

    _, _, bias_file = load_kbpath(dataset_path)

    settings = Settings(bias_file=bias_file, ex_file=None, bk_file=None, noisy=True)
    stats = Stats(info=settings.info)

    strategy = FedMDL(
        settings=settings,
        stats=stats,
        fraction_fit=1.0,
        fraction_evaluate=0.0,
        min_fit_clients=args.clients,
        min_available_clients=args.clients,
        min_evaluate_clients=0,
        with_suspension=(args.timing_mode == "wall"),
        timeout_seconds=args.timeout,
        combine_mode=args.combine_mode,
        # "Stop" button: the UI writes <output-dir>/STOP (core/run_control.py)
        stop_file=os.path.join(args.output_dir, "STOP"),
    )

    log(DEBUG, "Starting Flower server with FedMDL strategy.")

    parsed_address = parse_address(args.address)
    if not parsed_address:
        raise ValueError(f"Server IP address ({args.address}) cannot be parsed.")
    host, port, is_v6 = parsed_address
    address = f"[{host}]:{port}" if is_v6 else f"{host}:{port}"

    initialized_server, initialized_config = init_defaults(
        server=None,
        config=fl.server.ServerConfig(num_rounds=args.rounds),
        strategy=strategy,
        client_manager=None,
    )

    grpc_server = start_grpc_server(
        client_manager=initialized_server.client_manager(),
        server_address=address,
    )

    try:
        try:
            initialized_server.fit(
                num_rounds=initialized_config.num_rounds,
                timeout=initialized_config.round_timeout,
            )
        except EarlyStopSignal as signal:
            log(DEBUG, "Flower server stopped early: %s", signal)
    finally:
        log(INFO, "Disconnecting all clients.")
        initialized_server.disconnect_all_clients(timeout=5.0)
        grpc_server.stop(grace=1)

    save_server_result(output_directory=output_directory, strategy=strategy)
    log(DEBUG, "Flower server has stopped.")

    print("\n========== FINAL SOLUTION ==========")
    if strategy.solution_found and strategy.solution_program:
        for rule in strategy.solution_program:
            print(f"  {rule_to_text(rule)}")
    else:
        print("No improving program found.")


if __name__ == "__main__":
    main()

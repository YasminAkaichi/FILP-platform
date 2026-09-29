import argparse
import os
import sys
import json
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

POPPER_PATH = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "..",
        "symbolic",
        "popper-core",
    )
)

if POPPER_PATH not in sys.path:
    sys.path.insert(0, POPPER_PATH)


# Seulement après avoir configuré sys.path :
import flwr as fl

from flwr.common import parameters_to_ndarrays
from flwr.common.logger import log
from logging import DEBUG, INFO

from flwr.server.server import init_defaults
from flwr.server.superlink.fleet.grpc_bidi.grpc_server import start_grpc_server
from flwr.supercore.address import parse_address

from engines.collaboration.strategy.fedpopper import FedPopper, EarlyStopSignal

from popper.asp import ClingoGrounder, ClingoSolver
from popper.constrain import Constrain
from popper.core import Clause
from popper.federatedtester import FederatedTester
from popper.util import Settings, Stats, load_kbpath

if POPPER_PATH not in sys.path:
    sys.path.insert(0, POPPER_PATH)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..")
)

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start the FedPopper Flower server."
    )

    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help=(
            "Path to the server dataset. It can be relative to the "
            "fedpopper directory or absolute. "
            "Example: datasets/zendo1"
        ),
    )
    parser.add_argument(
    "--timing-mode",
    type=str,
    choices=["wall", "cpu"],
    default="wall",
    help=(
        "Timing mode: 'wall' uses perf_counter(), "
        "'cpu' uses process_time()."
    ),
    )
    parser.add_argument(
    "--output-dir",
    type=str,
    required=True,
    help="Directory where the server result JSON file will be written.",)

    parser.add_argument(
        "--clients",
        type=int,
        required=True,
        help="Number of federated clients expected by the server.",
    )

    parser.add_argument(
        "--rounds",
        type=int,
        default=10_000_000,
        help=(
            "Internal safety cap on Flower rounds — not a real stopping "
            "condition. The search actually stops when a solution is "
            "found or --timeout is reached (see EarlyStopSignal); this "
            "huge default just satisfies Flower's API, which requires a "
            "finite num_rounds. Not exposed in the UI."
        ),
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help=(
            "Seconds the Popper search is allowed to run before it stops "
            "and returns the best hypothesis found so far, if no exact "
            "solution has been found yet."
        ),
    )

    parser.add_argument(
        "--address",
        type=str,
        default="0.0.0.0:8080",
        help="Flower server address. Default: 0.0.0.0:8080.",
    )

    return parser.parse_args()


def resolve_dataset_path(dataset_argument: str) -> str:
    if os.path.isabs(dataset_argument):
        dataset_path = dataset_argument
    else:
        dataset_path = os.path.join(
            PROJECT_ROOT,
            dataset_argument,
        )

    dataset_path = os.path.abspath(dataset_path)

    if not os.path.isdir(dataset_path):
        raise FileNotFoundError(
            f"Server dataset directory not found: {dataset_path}"
        )

    return dataset_path


def print_final_solution(strategy: FedPopper) -> None:
    print("\n========== FINAL SOLUTION ==========")

    if strategy.exact_solution_found and strategy.solution_params:
        arrays = parameters_to_ndarrays(strategy.solution_params)

        if arrays and arrays[0].size > 0:
            print("Solution found:")

            for rule in arrays[0].tolist():
                print(f"  {rule}")
        else:
            print("Solution params empty.")

    elif strategy.best_hypothesis:
        print("No perfect solution — best hypothesis:")

        for rule in strategy.best_hypothesis:
            print(f"  {Clause.to_code(rule)}")

    else:
        print("No solution found.")

def save_server_result(
    output_directory: Path,
    strategy: FedPopper,
) -> None:
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    solution = None
    # exact_solution_found is only True when Popper actually found a
    # rule with outcome == ("all", "none") — NOT just whenever
    # solution_params is set, since that field also gets backfilled
    # from best_hypothesis as a fallback on timeout/exhausted search
    # (see FedPopper.aggregate_fit). Using solution_params truthiness
    # here used to mark every best-effort run as "solution found".
    solution_found = bool(strategy.exact_solution_found)

    if strategy.solution_params:
        arrays = parameters_to_ndarrays(
            strategy.solution_params
        )

        if arrays and arrays[0].size > 0:
            solution_rules = [
                str(rule)
                for rule in arrays[0].tolist()
            ]

            solution = "\n".join(solution_rules)

    elif strategy.best_hypothesis:
        solution_rules = [
            Clause.to_code(rule)
            for rule in strategy.best_hypothesis
        ]

        solution = "\n".join(solution_rules)

    total_time = (
        strategy.timer() - strategy.global_start
    )

    federation_ratio = (
        strategy.tFedPopper / total_time
        if total_time > 0
        else 0.0
    )
    startup_time = float(
    strategy.startup_time
    if strategy.startup_time is not None
    else 0.0
    )

    learning_time = float(
        strategy.learning_time
        if strategy.learning_time is not None
        else 0.0
    )
    result = {
    "solution": solution,
    "solution_found": solution_found,
    "total_time": float(total_time),
    "startup_time": startup_time,
    "learning_time": learning_time,
    "popper_time": float(strategy.tCentralPopper),
    "federation_time": float(strategy.tFedPopper),
    "federation_ratio": float(federation_ratio),
    "number_of_rounds": int(
        getattr(strategy, "last_round", 0)
    ),
    "number_of_programs": int(
        getattr(strategy.stats, "total_programs", 0)
    ),
    "final_score": float(
        strategy.best_score
        if strategy.best_score is not None
        else 0.0
    ),
    }

    result_path = (
        output_directory
        / "server_result.json"
    )

    print(
    "[DEBUG SERVER RESULT] "
    f"startup={startup_time:.4f}, "
    f"learning={learning_time:.4f}",
    flush=True,
)

    print(
        f"[DEBUG SERVER FILE] {__file__}",
        flush=True,
    )

    result_path.write_text(
        json.dumps(
            result,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Every hypothesis actually tested, in order, with its score — lets
    # the launcher persist a record that "the reported solution is the
    # best-scoring one" can be checked directly instead of trusted on
    # faith or dug out of terminal logs.
    hypothesis_log_path = (
        output_directory
        / "hypothesis_log.json"
    )

    hypothesis_log_path.write_text(
        json.dumps(
            strategy.hypothesis_log,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"[Server] Result saved to: {result_path}",
        flush=True,
    )
def main() -> None:
    args = parse_arguments()
    output_directory = Path(
        args.output_dir
    ).resolve()

    if args.clients < 1:
        raise ValueError(
            "The number of clients must be at least 1."
        )

    if args.rounds < 1:
        raise ValueError(
            "The number of rounds must be at least 1."
        )

    dataset_path = resolve_dataset_path(args.dataset)

    print("========== FEDPOPPER SERVER ==========", flush=True)
    print(f"Dataset           : {dataset_path}", flush=True)
    print(f"Number of clients : {args.clients}", flush=True)
    print(f"Maximum rounds    : {args.rounds}", flush=True)
    print(f"Server address    : {args.address}", flush=True)

    _, _, bias_file = load_kbpath(dataset_path)

    settings = Settings(
        bias_file,
        None,
        None,
    )

    tester = FederatedTester(settings)
    stats = Stats(log_best_programs=settings.info)
    solver = ClingoSolver(settings)
    grounder = ClingoGrounder()
    constrainer = Constrain()

    strategy = FedPopper(
        settings=settings,
        stats=stats,
        solver=solver,
        grounder=grounder,
        tester=tester,
        constrainer=constrainer,
        fraction_fit=1.0,
        # Flower's separate federated-evaluation phase (configure_evaluate
        # -> client.evaluate() -> aggregate_evaluate) re-tests the same
        # rules a second time every round, purely to feed Flower's own
        # History object for logging. Nothing in FedPopper reads that
        # result — early_stop, best_hypothesis and solution_params all
        # come from aggregate_fit() only — and the History return value
        # of server.fit() isn't even captured anymore (see the early-stop
        # fix above). Measured at ~60-65% of Learning time on trains1000
        # for zero functional benefit, so it's disabled: fraction_evaluate
        # =0.0 makes configure_evaluate() return [] immediately, and
        # Flower's evaluate_round() then returns None without contacting
        # any client (see flwr.server.server.Server.evaluate_round).
        fraction_evaluate=0.0,
        min_fit_clients=args.clients,
        min_available_clients=args.clients,
        min_evaluate_clients=0,
        fit_metrics_aggregation_fn=None,
        with_suspension=(args.timing_mode == "wall"),
        timeout_seconds=args.timeout,
    )

    log(
        DEBUG,
        "Starting Flower server with FedPopper strategy.",
    )

    # NOTE: we deliberately don't call fl.server.start_server() here.
    # That helper calls run_fl() -> server.fit(...) with no try/except
    # around it, so an exception raised out of the round loop (our
    # EarlyStopSignal, used to stop Flower as soon as Popper converges
    # instead of coasting through the remaining configured rounds)
    # would skip BOTH server.disconnect_all_clients() and
    # grpc_server.stop(grace=1). Without that graceful shutdown, the
    # connected Flower clients never receive a ReconnectIns and can
    # sit blocked on their gRPC stream for a long time (bounded only
    # by gRPC's keepalive, ~210s) instead of exiting immediately -
    # which is exactly what we saw freeze the launcher/UI in testing.
    #
    # So we inline start_server()'s logic ourselves and wrap only the
    # round loop, keeping the graceful-shutdown calls in a `finally`.
    parsed_address = parse_address(args.address)

    if not parsed_address:
        raise ValueError(
            f"Server IP address ({args.address}) cannot be parsed."
        )

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
            # Expected, not an error: the Popper loop finished and
            # configure_fit() raised this to stop Flower immediately.
            log(DEBUG, "Flower server stopped early: %s", signal)
    finally:
        # Always run Flower's normal graceful shutdown, early-stop or
        # not, so connected clients get told to disconnect right away.
        #
        # IMPORTANT: don't reuse initialized_config.round_timeout here.
        # It's None by default, and reconnect_clients() waits on
        # concurrent.futures.wait(..., timeout=None) — with a None
        # per-client timeout too, a single client that doesn't answer
        # (e.g. one that already crashed) blocks this call, and thus
        # the whole launcher/UI, forever. Use a bounded timeout so
        # shutdown always completes even if a client is unresponsive.
        log(INFO, "Disconnecting all clients.")
        initialized_server.disconnect_all_clients(
            timeout=5.0,
        )
        grpc_server.stop(grace=1)

    strategy._print_performance_summary(force=True)

    save_server_result(
    output_directory=output_directory,
    strategy=strategy,
     )
    log(
        DEBUG,
        "Flower server has stopped.",
    )

    print_final_solution(strategy)


if __name__ == "__main__":
    main()
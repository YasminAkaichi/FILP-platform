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
from logging import DEBUG

from engines.collaboration.strategy.fedpopper import FedPopper

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
        default=35000,
        help="Maximum number of Flower rounds. Default: 35000.",
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

    if strategy.solution_params:
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
    solution_found = False

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
            solution_found = True

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
        fraction_evaluate=1.0,
        min_fit_clients=args.clients,
        min_available_clients=args.clients,
        min_evaluate_clients=args.clients,
        fit_metrics_aggregation_fn=None,
        with_suspension=(args.timing_mode == "wall"),
    )

    log(
        DEBUG,
        "Starting Flower server with FedPopper strategy.",
    )

    fl.server.start_server(
        server_address=args.address,
        config=fl.server.ServerConfig(
            num_rounds=args.rounds,
        ),
        strategy=strategy,
    )

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
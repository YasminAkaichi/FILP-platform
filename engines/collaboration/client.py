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
PROJECT_ROOT = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..")
)

if POPPER_PATH not in sys.path:
    sys.path.insert(0, POPPER_PATH)

if POPPER_PATH not in sys.path:
    sys.path.insert(0, POPPER_PATH)
import json
import argparse
import atexit
import logging
import os
import re
import time

import flwr as fl
import numpy as np

from popper.core import Literal
from popper.loop import calc_score, decide_outcome
from popper.tester import Tester
from popper.util import Settings, Stats, format_conf_matrix, load_kbpath


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


OUTCOME_ENCODING = {
    "all": 1,
    "some": 2,
    "none": 3,
}


def parse_arguments() -> argparse.Namespace:
    """
    Read the client configuration from the command line.

    Example:
        python3 client.py \
            --client-id 1 \
            --dataset datasets/zendo1_part1
    """
    parser = argparse.ArgumentParser(
        description="Start a FedPopper Flower client."
    )

    parser.add_argument(
        "--client-id",
        type=int,
        required=True,
        help="Identifier of the federated client, for example 1, 2 or 3.",
    )

    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help=(
            "Path to the client's dataset, relative to the fedpopper directory "
            "or as an absolute path. "
            "Example: datasets/zendo1_part1"
        ),
    )

    parser.add_argument(
        "--server-address",
        type=str,
        default="localhost:8080",
        help="Address of the Flower server. Default: localhost:8080",
    )
    parser.add_argument(
    "--output-dir",
    type=str,
    required=True,
    help="Directory where the client result JSON file will be written.",)

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
            f"Dataset directory not found: {dataset_path}"
        )

    return dataset_path

def transform_rule_to_tester_format(rule_str: str):
    """
    Transform a Prolog rule received as text into the representation expected
    by the Popper tester.

    Example:
        target(A) :- relation(A,B), property(B).
    """
    head_body = rule_str.split(":-", maxsplit=1)

    if len(head_body) != 2:
        raise ValueError(f"Invalid rule format: {rule_str}")

    head_str = head_body[0].strip()
    body_str = head_body[1].strip().rstrip(".")

    body_literals = re.findall(r"\w+\(.*?\)", body_str)

    head = Literal.from_string(head_str)
    body = tuple(
        Literal.from_string(literal)
        for literal in body_literals
    )

    return head, body


class FlowerClient(fl.client.NumPyClient):
    def __init__(
        self,
        client_id: int,
        tester: Tester,
        stats: Stats,
        number_of_positive_examples: int,
        number_of_negative_examples: int,
        output_directory: Path,
        dataset_path: Path,
    ) -> None:
        self.client_id = client_id
        self.tester = tester
        self.stats = stats
        self.output_directory = output_directory
        self.number_of_positive_examples = number_of_positive_examples
        self.number_of_negative_examples = number_of_negative_examples

        self.current_rules = []

        self.num_evaluations = 0
        self.total_eval_wall = 0.0
        self.total_eval_cpu = 0.0
        self.dataset_path = dataset_path

    def get_parameters(self, config):
        """
        The client does not train numerical parameters.

        An empty NumPy array is returned only to respect Flower's NumPyClient
        interface.
        """
        return [np.array([], dtype=np.int64)]

    def set_parameters(self, parameters) -> None:
        """
        Convert the rules received from the server into Popper literals.
        """
        if (
            not parameters
            or len(parameters) == 0
            or parameters[0].size == 0
        ):
            self.current_rules = []
            return

        rules_array = parameters[0]

        if rules_array.dtype.kind not in {"U", "S", "O"}:
            self.current_rules = []
            return

        received_rules = rules_array.tolist()

        parsed_rules = []

        for rule in received_rules:
            try:
                parsed_rule = transform_rule_to_tester_format(str(rule))
                parsed_rules.append(parsed_rule)
            except ValueError as error:
                log.warning(
                    "Client %s could not parse rule %r: %s",
                    self.client_id,
                    rule,
                    error,
                )

        self.current_rules = parsed_rules

    def print_client_summary(self) -> None:
        """
        Print a summary when the client process stops.
        """
        total_examples = (
            self.number_of_positive_examples
            + self.number_of_negative_examples
        )

        print("\n========== CLIENT SUMMARY ==========", flush=True)
        print(
            f"Client ID              : {self.client_id}",
            flush=True,
        )
        print(
            f"Local examples         : {total_examples}",
            flush=True,
        )
        print(
            f"Pos examples           : "
            f"{self.number_of_positive_examples}",
            flush=True,
        )
        print(
            f"Neg examples           : "
            f"{self.number_of_negative_examples}",
            flush=True,
        )
        print(
            f"Number of evaluations  : {self.num_evaluations}",
            flush=True,
        )
        print(
            f"Total local eval wall  : "
            f"{self.total_eval_wall:.4f}s",
            flush=True,
        )
        print(
            f"Total local eval CPU   : "
            f"{self.total_eval_cpu:.4f}s",
            flush=True,
        )

        if self.num_evaluations > 0:
            average_wall = (
                self.total_eval_wall / self.num_evaluations
            )
            average_cpu = (
                self.total_eval_cpu / self.num_evaluations
            )

            print(
                f"Avg local eval wall    : {average_wall:.4f}s",
                flush=True,
            )
            print(
                f"Avg local eval CPU     : {average_cpu:.4f}s",
                flush=True,
            )
    def save_client_result(self) -> None:
        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
        print(
            f"[Client {self.client_id}] Saving result...",
            flush=True,
        )
        if self.last_confusion_matrix is None:
            tp = fn = tn = fp = 0
        else:
            tp, fn, tn, fp = self.last_confusion_matrix

        average_wall = (
            self.total_eval_wall / self.num_evaluations
            if self.num_evaluations > 0
            else 0.0
        )

        average_cpu = (
            self.total_eval_cpu / self.num_evaluations
            if self.num_evaluations > 0
            else 0.0
        )

        accepted_solution = (
            self.last_epsilon_positive == "all"
            and self.last_epsilon_negative == "none"
        )

        result = {
            "client_id": int(self.client_id),
            "dataset_partition": str(self.dataset_path),
            "number_of_examples": int(
                self.number_of_positive_examples
                + self.number_of_negative_examples
            ),
            "number_of_positive_examples": int(
                self.number_of_positive_examples
            ),
            "number_of_negative_examples": int(
                self.number_of_negative_examples
            ),
            "number_of_evaluations": int(self.num_evaluations),
            "total_eval_wall": float(self.total_eval_wall),
            "total_eval_cpu": float(self.total_eval_cpu),
            "average_eval_wall": float(average_wall),
            "average_eval_cpu": float(average_cpu),
            "final_epsilon_positive": self.last_epsilon_positive,
            "final_epsilon_negative": self.last_epsilon_negative,
            "accepted_solution": bool(accepted_solution),
            "final_score": float(self.last_score or 0),
            "tp": int(tp),
            "fn": int(fn),
            "tn": int(tn),
            "fp": int(fp),
        }

        result_path = (
            self.output_directory
            / f"client_{self.client_id}_result.json"
        )

        result_path.write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )

        print(
            f"[Client {self.client_id}] Result saved to: {result_path}",
            flush=True,
        )
    def fit(self, parameters, config):
        """
        Evaluate the hypothesis received from the server and return symbolic
        feedback plus the local score.
        """
        round_id = config.get("round", -1)

        print(
            f"\nCLIENT {self.client_id} — ROUND {round_id}",
            flush=True,
        )

        self.set_parameters(parameters)

        if not self.current_rules:
            payload = np.array(
                [
                    OUTCOME_ENCODING["none"],
                    OUTCOME_ENCODING["none"],
                    0,
                ],
                dtype=np.int64,
            )

            return [payload], 1, {}

        eval_wall_start = time.perf_counter()
        eval_cpu_start = time.process_time()

        confusion_matrix = self.tester.test(self.current_rules)

        inconsistent_rules = []
        totally_incomplete_rules = []

        for rule in self.current_rules:
            inconsistent_rules.append(
                bool(self.tester.is_inconsistent(rule))
            )

            totally_incomplete_rules.append(
                bool(self.tester.is_totally_incomplete(rule))
            )
                
        
      
        eval_wall = time.perf_counter() - eval_wall_start
        eval_cpu = time.process_time() - eval_cpu_start

        self.num_evaluations += 1
        self.total_eval_wall += eval_wall
        self.total_eval_cpu += eval_cpu

        tp, fn, tn, fp = confusion_matrix


        print(
            f"Local eval time: wall={eval_wall:.4f}s "
            f"cpu={eval_cpu:.4f}s",
            flush=True,
        )

        print(
            f"Local Result: TP={tp} FN={fn} TN={tn} FP={fp}",
            flush=True,
        )

        eps_plus, eps_minus = decide_outcome(confusion_matrix)
        score = calc_score(confusion_matrix)
        self.last_confusion_matrix = confusion_matrix
        self.last_epsilon_positive = str(eps_plus)
        self.last_epsilon_negative = str(eps_minus)
        self.last_score = int(score)

        print(
            f"Feedback: e+={eps_plus}, "
            f"e-={eps_minus}, score={score}",
            flush=True,
        )

        print(
            format_conf_matrix(confusion_matrix),
            flush=True,
        )

        payload = np.array(
            [
                OUTCOME_ENCODING[str(eps_plus).lower()],
                OUTCOME_ENCODING[str(eps_minus).lower()],
                int(score),
            ],
            dtype=np.int64,
        )

        metrics = {
            "client_id": self.client_id,
            "round": round_id,
            "tp": int(tp),
            "fn": int(fn),
            "tn": int(tn),
            "fp": int(fp),
            "score": int(score),
            "evaluation_wall_seconds": float(eval_wall),
            "evaluation_cpu_seconds": float(eval_cpu),
            "inconsistent_rules": json.dumps(inconsistent_rules),
            "totally_incomplete_rules": json.dumps(
                totally_incomplete_rules
            ),
        }

        return [payload], 1, metrics

    def evaluate(self, parameters, config):
        """
        Evaluate the received hypothesis for Flower's evaluation phase.
        """
        self.set_parameters(parameters)

        if not self.current_rules:
            return 1.0, 0, {
                "client_id": self.client_id,
                "accuracy": 0.0,
            }

        confusion_matrix = self.tester.test(self.current_rules)

        
        tp, fn, tn, fp = confusion_matrix
        
        total = tp + fn + tn + fp

        accuracy = (
            (tp + tn) / total
            if total > 0
            else 0.0
        )

        loss = float(1.0 - accuracy)

        metrics = {
            "client_id": self.client_id,
            "tp": int(tp),
            "fn": int(fn),
            "tn": int(tn),
            "fp": int(fp),
            "accuracy": float(accuracy),
        }

        return loss, total, metrics


def main() -> None:
    args = parse_arguments()

    dataset_path = resolve_dataset_path(args.dataset)
    output_directory = Path(args.output_dir).resolve()

    print("========== FEDPOPPER CLIENT ==========", flush=True)
    print(f"Client ID      : {args.client_id}", flush=True)
    print(f"Dataset        : {dataset_path}", flush=True)
    print(f"Flower server  : {args.server_address}", flush=True)

    bk_file, ex_file, bias_file = load_kbpath(dataset_path)

    settings = Settings(
        bias_file,
        ex_file,
        bk_file,
    )

    tester = Tester(settings)
    stats = Stats(log_best_programs=settings.info)

    settings.num_pos = len(tester.pos)
    settings.num_neg = len(tester.neg)

    client = FlowerClient(
    client_id=args.client_id,
    tester=tester,
    stats=stats,
    number_of_positive_examples=settings.num_pos,
    number_of_negative_examples=settings.num_neg,
    dataset_path=Path(dataset_path),
    output_directory=output_directory,
)

    #atexit.register(client.print_client_summary)
    #atexit.register(client.save_client_result)

    try:
        fl.client.start_client(
            server_address=args.server_address,
            client=client.to_client(),
        )
    finally:
        client.print_client_summary()
        client.save_client_result()
        


if __name__ == "__main__":
    main()
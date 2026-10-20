"""
FedMDL Flower client. Mirrors engines/collaboration/client.py's structure;
the `fit()` logic differs because FedMDL's server-client protocol is
simpler than FedPopper's (no all/some/none outcome, no inconsistent/
totally_incomplete rule feedback) — see
engines/mdl_federation/strategy/fedmdl.py's module docstring for why.

Three round "phases", distinguished by `config["phase"]` (set by the server
in FitIns.config). The examples never leave the client. What does leave
depends on config["mode"]:
  - "indices" (default): for each candidate, the list of local positions of
    the covered examples (the server knows how many examples each client
    has and who owns which position, never what they are);
  - "signatures" (privacy variant): only counts, then one signature table.

  - "register": round 1 only. No candidate rule exists yet — the server is
    just collecting every client's local (num_pos, num_neg) example count
    to build one consistent global index space (see FedMDL.
    _register_client_counts). This client responds with those two counts
    and its own client_id, nothing else.

  - "test": config["rule"] holds one candidate rule as plain text (the
    same format popper_mdl.util.format_rule produces) and config["cand_id"]
    its id. This client parses it back into a popper_mdl Literal-based rule
    (engines.mdl_federation.rule_codec.parse_rule, using this client's own
    `settings.directions`, built from the same bias.pl the server used),
    tests it locally via popper_mdl.tester.Tester.test_single_rule_pos /
    ..._neg, and reports the covered local positions ("indices" mode) or
    only the two counts (|P|, |N|), keeping the coverage locally
    ("signatures" mode).

  - "signatures" (signatures mode only): last round. The server sends the ids of the pool (the
    promising candidates). The client replies with a table
    {signature -> (n_pos, n_neg)}, where the signature of a local example
    is the set of pool rules covering it. The server sums the tables of all
    clients and runs an exact weighted combine on them
    (engines.mdl_federation.signature_combiner): same optimum as a combine
    over per-example coverage sets, without any example identifier.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
POPPER_MDL_PATH = os.path.join(PROJECT_ROOT, "symbolic", "Popper-v3")

if POPPER_MDL_PATH not in sys.path:
    sys.path.insert(0, POPPER_MDL_PATH)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import flwr as fl
import numpy as np

from popper_mdl.tester import Tester
from popper_mdl.util import Settings, load_kbpath

from engines.mdl_federation.rule_codec import parse_rule


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start a FedMDL Flower client.")
    parser.add_argument("--client-id", type=int, required=True)
    parser.add_argument("--dataset", type=str, required=True, help="Path to this client's local dataset partition")
    parser.add_argument("--server-address", type=str, default="localhost:8080")
    parser.add_argument("--output-dir", type=str, required=True)
    return parser.parse_args()


def resolve_dataset_path(dataset_argument: str) -> str:
    dataset_path = (
        dataset_argument
        if os.path.isabs(dataset_argument)
        else os.path.join(PROJECT_ROOT, dataset_argument)
    )
    dataset_path = os.path.abspath(dataset_path)
    if not os.path.isdir(dataset_path):
        raise FileNotFoundError(f"Dataset directory not found: {dataset_path}")
    return dataset_path


class FedMDLClient(fl.client.NumPyClient):
    def __init__(self, client_id: int, tester: Tester, settings, output_directory: Path):
        self.client_id = client_id
        self.tester = tester
        self.settings = settings
        self.output_directory = output_directory

        self.num_pos = len(tester.pos_index)
        self.num_neg = len(tester.neg_index)

        self.num_rounds_tested = 0
        self.total_eval_wall = 0.0

        # Every candidate this client was asked to test, kept for the
        # client-side result file — same spirit as the other engines'
        # client_N_result.json, so the Dataset/Clients tabs have something
        # to show for FedMDL runs too.
        self.tested_log: list[dict] = []

        # candidate id -> (local positive indices, local negative indices)
        # covered. Stays on the client; only aggregated counts are sent.
        self.coverage: dict[int, tuple[frozenset, frozenset]] = {}

        # The best (highest positive-coverage, then lowest negative-
        # coverage) rule seen locally, purely for this client's own
        # result summary — the server's combine step is the real decision
        # maker, this client never finds out what the FINAL global
        # solution was (same "clients never see the end result" shape as
        # the other federated engines' per-round clients).
        self.best_local_pos_covered = 0
        self.best_local_neg_covered = 0
        self.best_local_rule_text = None

    def get_parameters(self, config):
        return [np.array([], dtype="<U1")]

    def set_parameters(self, parameters) -> None:
        pass  # FedMDL never sends numeric parameters, only FitIns.config

    def fit(self, parameters, config):
        phase = config.get("phase", "test")

        if phase == "register":
            return (
                [np.array([], dtype="<U1")],
                1,
                {
                    "client_id": str(self.client_id),
                    "num_pos": self.num_pos,
                    "num_neg": self.num_neg,
                },
            )

        if phase == "signatures":
            return self._signature_table(config)

        rule_text = config.get("rule")
        if not rule_text:
            return (
                [np.array([], dtype="<U1")],
                1,
                {
                    "client_id": str(self.client_id),
                    "pos_count": 0,
                    "neg_count": 0,
                },
            )

        eval_start = time.perf_counter()

        rule = parse_rule(rule_text, self.settings.directions)
        prog = frozenset([rule])

        # Both coverage sets are needed locally: the positives AND the
        # negatives, even when the rule covers no local positive — the
        # rule can still be promising globally, and then its false
        # positives on THIS client must be counted.
        pos_covered = sorted(self.tester.test_single_rule_pos(prog))
        neg_covered = sorted(self.tester.test_single_rule_neg(prog))

        mode = config.get("mode", "indices")

        # "signatures" mode: the coverage never leaves this client. It is
        # kept under the candidate's id so that, at the end, the server can
        # ask for the signature table of the pool (see _signature_table).
        cand_id = config.get("cand_id")
        if mode == "signatures" and cand_id is not None and (pos_covered or neg_covered):
            self.coverage[int(cand_id)] = (frozenset(pos_covered), frozenset(neg_covered))

        eval_wall = time.perf_counter() - eval_start
        self.total_eval_wall += eval_wall
        self.num_rounds_tested += 1

        self.tested_log.append(
            {
                "round": config.get("round"),
                "rule": rule_text,
                "positive_covered": len(pos_covered),
                "negative_covered": len(neg_covered),
            }
        )

        if len(pos_covered) > self.best_local_pos_covered or (
            len(pos_covered) == self.best_local_pos_covered
            and len(neg_covered) < self.best_local_neg_covered
        ):
            self.best_local_pos_covered = len(pos_covered)
            self.best_local_neg_covered = len(neg_covered)
            self.best_local_rule_text = rule_text

        if mode == "indices":
            # The answer to "is my example i covered by this rule?" for
            # every local example, as the list of covered LOCAL positions.
            # The server only knows which client owns which positions (its
            # inventory); it never sees the examples themselves.
            return (
                [np.array([], dtype="<U1")],
                1,
                {
                    "client_id": str(self.client_id),
                    "pos_covered": json.dumps(pos_covered),
                    "neg_covered": json.dumps(neg_covered),
                },
            )

        # "signatures" mode: only two COUNTS per candidate.
        return (
            [np.array([], dtype="<U1")],
            1,
            {
                "client_id": str(self.client_id),
                "pos_count": len(pos_covered),
                "neg_count": len(neg_covered),
            },
        )

    def _signature_table(self, config):
        """
        Final round. The server sends the ids of the candidates it kept in
        its pool. For every local example we compute its *signature* (the
        sorted ids of the pool rules that cover it) and return, for each
        distinct signature, how many local positives / negatives have it.
        Only these counts leave the client — no example identifier — and
        they are exactly what the server's weighted combine needs.
        """
        pool_ids = sorted(int(i) for i in json.loads(config.get("pool", "[]")))

        pos_by_example: dict[int, list[int]] = {}
        neg_by_example: dict[int, list[int]] = {}
        for cand_id in pool_ids:
            pos_cov, neg_cov = self.coverage.get(cand_id, (frozenset(), frozenset()))
            for i in pos_cov:
                pos_by_example.setdefault(i, []).append(cand_id)
            for i in neg_cov:
                neg_by_example.setdefault(i, []).append(cand_id)

        pos_table: Counter = Counter()
        for i in self.tester.pos_index:
            pos_table[tuple(pos_by_example.get(i, ()))] += 1
        neg_table: Counter = Counter()
        for i in self.tester.neg_index:
            neg_table[tuple(neg_by_example.get(i, ()))] += 1

        return (
            [np.array([], dtype="<U1")],
            1,
            {
                "client_id": str(self.client_id),
                "pos_sig": json.dumps([[list(s), n] for s, n in pos_table.items()]),
                "neg_sig": json.dumps([[list(s), n] for s, n in neg_table.items()]),
            },
        )

    def evaluate(self, parameters, config):
        return 0.0, 1, {"client_id": self.client_id}

    def save_client_result(self) -> None:
        self.output_directory.mkdir(parents=True, exist_ok=True)
        result = {
            "client_id": self.client_id,
            "dataset_partition": str(self.output_directory),
            "number_of_examples": self.num_pos + self.num_neg,
            "number_of_positive_examples": self.num_pos,
            "number_of_negative_examples": self.num_neg,
            "number_of_evaluations": self.num_rounds_tested,
            "total_eval_wall": self.total_eval_wall,
            "average_eval_wall": (
                self.total_eval_wall / self.num_rounds_tested
                if self.num_rounds_tested
                else 0.0
            ),
            "best_local_rule": self.best_local_rule_text,
            "best_local_positive_covered": self.best_local_pos_covered,
            "best_local_negative_covered": self.best_local_neg_covered,
        }
        result_path = self.output_directory / f"client_{self.client_id}_result.json"
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"[FedMDL Client {self.client_id}] Result saved to: {result_path}", flush=True)

    def print_client_summary(self) -> None:
        print(f"\n========== FEDMDL CLIENT {self.client_id} SUMMARY ==========", flush=True)
        print(f"Local examples      : {self.num_pos} positive, {self.num_neg} negative", flush=True)
        print(f"Candidates tested   : {self.num_rounds_tested}", flush=True)
        print(f"Best local rule     : {self.best_local_rule_text}", flush=True)


def main() -> None:
    args = parse_arguments()

    dataset_path = resolve_dataset_path(args.dataset)
    output_directory = Path(args.output_dir).resolve()

    print("========== FEDMDL CLIENT ==========", flush=True)
    print(f"Client ID      : {args.client_id}", flush=True)
    print(f"Dataset        : {dataset_path}", flush=True)
    print(f"Flower server  : {args.server_address}", flush=True)

    bk_file, ex_file, bias_file = load_kbpath(dataset_path)

    settings = Settings(bias_file=bias_file, ex_file=ex_file, bk_file=bk_file, noisy=True)
    tester = Tester(settings)

    client = FedMDLClient(
        client_id=args.client_id,
        tester=tester,
        settings=settings,
        output_directory=output_directory,
    )

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

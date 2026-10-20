"""
Local evaluation of FedMDL's final program on ONE client's partition.

Run by the launcher after the federated run (simulation side: the launcher
owns every partition directory). The program is evaluated exactly as the
client's Tester would: per-clause coverage and the whole-program confusion
matrix on the client's local examples. Nothing here is sent back to the
server — it only feeds the Clients tab of the dashboard.

    python -m engines.mdl_federation.evaluate_final \
        --dataset <partition dir> --solution-file <rules.pl> --output <json>
"""

from __future__ import annotations

import argparse
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
POPPER_MDL_PATH = os.path.join(PROJECT_ROOT, "symbolic", "Popper-v3")

for path in (POPPER_MDL_PATH, PROJECT_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from popper_mdl.tester import Tester
from popper_mdl.util import Settings, load_kbpath

from engines.mdl_federation.rule_codec import parse_rule


def evaluate(dataset: str, rules_text: list[str]) -> dict:
    bk_file, ex_file, bias_file = load_kbpath(dataset)
    settings = Settings(bias_file=bias_file, ex_file=ex_file, bk_file=bk_file, noisy=True)
    tester = Tester(settings)

    num_pos = len(tester.pos_index)
    num_neg = len(tester.neg_index)

    covered_pos: set = set()
    covered_neg: set = set()
    clauses = []

    for text in rules_text:
        prog = frozenset([parse_rule(text, settings.directions)])
        pos = set(tester.test_single_rule_pos(prog))
        neg = set(tester.test_single_rule_neg(prog))
        covered_pos |= pos
        covered_neg |= neg
        clauses.append(
            {
                "clause": text,
                "positive_covered": len(pos),
                "negative_covered": len(neg),
            }
        )

    tp = len(covered_pos)
    fp = len(covered_neg)
    return {
        "num_pos": num_pos,
        "num_neg": num_neg,
        "tp": tp,
        "fn": num_pos - tp,
        "fp": fp,
        "tn": num_neg - fp,
        "clauses": clauses,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--solution-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.solution_file, encoding="utf-8") as handle:
        rules = [line.strip() for line in handle if ":-" in line]

    result = evaluate(args.dataset, rules)

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)


if __name__ == "__main__":
    main()

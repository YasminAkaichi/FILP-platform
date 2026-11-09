"""Evaluate programs with the code of the Coordination client, outside any run.

scripts/check_eval_timeout.py evaluates a program with Popper's Tester directly
and finds the true score. The platform records other scores for some programs
(for example 437 to 451 for a program whose true score is 427). This script
runs the evaluation function of the client of the platform
(engines/coordination/clipopper.py, popper_test_hypothesis_final) on the same
data, alone on the machine, with the limits of the launcher. Two cases:

  * it returns the true score  -> the code of the client is right and the
    difference comes from the conditions of a run (load, concurrency);
  * it returns the recorded score -> the difference comes from the code of the
    client (parsing of the program, order of the literals, ...).

Run it with the same variables as the launcher:

    PYTHONHASHSEED=0 FILP_EVAL_TIMEOUT=0.1 python scripts/check_client_path.py \
        --dataset-dir datasets/generated/trains1000/iid_1_seed_42/trains1000_part1 \
        "f(A):-has_load(E,C),has_load(B,C),has_car(A,E),triangle(D),has_load(B,D)."
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "symbolic" / "popper-core"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-dir", required=True, help="directory with bias.pl, bk.pl, exs.pl")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("program", nargs="+", help="a program: one clause per argument")
    args = parser.parse_args()

    from engines.coordination.clipopper import initialisation, popper_test_hypothesis_final

    directory = Path(args.dataset_dir)
    if not directory.is_absolute():
        directory = ROOT / directory
    _, tester, stats = initialisation(0, str(directory))

    for repeat in range(1, args.repeats + 1):
        result = popper_test_hypothesis_final(list(args.program), tester, stats)
        positive, negative, score, _, _, matrix, wall, _ = result
        print(f"[repeat {repeat}] outcome ({positive}, {negative}), score {score}, "
              f"matrix (tp, fn, tn, fp) = {matrix}, evaluation {wall:.2f} s")


if __name__ == "__main__":
    main()

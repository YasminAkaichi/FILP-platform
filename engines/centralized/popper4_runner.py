"""
Centralized (non-federated) Popper 4 run.

Runs Popper 4 (symbolic/popper-v4) once, on the whole dataset, with no
clients and no server. It is the counterpart of engines/centralized/runner.py
(Popper 1.1.0, popper-core) and writes the same server_result.json.

Popper 4 and popper-core both install a package called `popper`, so they can
never be imported in the same process: this runner is spawned as its own
subprocess by core/launcher.py::_run_centralized and puts popper-v4 first on
sys.path. Popper 4 also implements its timeout with signal.alarm() (same
mechanism as popper-core), so the "Stop" button works the same way
(see stop_support.py).

Popper 4 needs SWI-Prolog (through janus_swi), bitarray and python-sat.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
POPPER_V4_PATH = PROJECT_ROOT / "symbolic" / "popper-v4"

# popper-v4 must win over any other copy of the `popper` package.
sys.path.insert(0, str(POPPER_V4_PATH))
sys.path.insert(1, str(PROJECT_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Centralized (non-federated) Popper 4 run")
    parser.add_argument("--dataset", required=True, help="Path to the dataset directory (exs.pl / bk.pl / bias.pl)")
    parser.add_argument("--timeout", type=float, default=25.0, help="Max search time in seconds")
    parser.add_argument("--output-dir", required=True, help="Directory to write server_result.json into")
    args = parser.parse_args()

    dataset_directory = Path(args.dataset).resolve()
    output_directory = Path(args.output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)

    for filename in ("bias.pl", "bk.pl", "exs.pl"):
        if not (dataset_directory / filename).is_file():
            raise FileNotFoundError(
                f"Invalid Popper dataset {dataset_directory}: missing {filename}"
            )

    from popper.loop import learn_solution
    from popper.util import Settings, format_rule

    settings = Settings(
        kbpath=str(dataset_directory),
        cmd_line=False,
        timeout=int(args.timeout),
        show_stats=False,
        # Same evaluation limit as the other engines (set by the launcher).
        eval_timeout=float(os.environ.get("FILP_EVAL_TIMEOUT", "0.001")),
    )

    # Popper 4 can ask for the recall of a relation it has removed from its
    # table (see engines/consensus/learners/popper_trainer.py): unknown
    # relations default to a large recall, which only orders them last.
    settings.recall = defaultdict(lambda: 10**9, settings.recall)

    # "Stop" button: makes Popper return its best program so far, exactly as
    # its own timeout would (see stop_support.py).
    from engines.centralized.stop_support import install_stop_watcher, search_running

    install_stop_watcher(output_directory)

    start_time = time.perf_counter()
    with search_running():
        program, score, stats = learn_solution(settings)
    total_time = time.perf_counter() - start_time

    hypothesis_code = (
        "\n".join(format_rule(rule) for rule in program) if program else None
    )

    # Popper 4 scores a program as (tp, fn, tn, fp, size).
    if program and score is not None and len(score) >= 4:
        tp, fn, tn, fp = (int(value) for value in score[:4])
    else:
        tp = fn = tn = fp = 0

    # A complete and consistent program is a solution; otherwise Popper 4
    # returns the best program found before the timeout (or the stop).
    solution_found = bool(program) and fn == 0 and fp == 0

    total_predictions = tp + fn + tn + fp
    accuracy = (tp + tn) / total_predictions if total_predictions else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    duration_summary = [
        {
            "operation": summary.operation,
            "called": summary.called,
            "total": summary.total,
            "mean": summary.mean,
            "maximum": summary.maximum,
        }
        for summary in stats.duration_summary()
    ]

    result = {
        "solution": hypothesis_code,
        "solution_found": solution_found,
        "total_time": total_time,
        "startup_time": 0.0,
        "learning_time": total_time,
        "popper_time": total_time,
        "federation_time": 0.0,
        "federation_ratio": 0.0,
        "number_of_rounds": 1,
        "number_of_programs": stats.total_programs,
        "final_score": float(tp + tn),
        "tp": tp,
        "fn": fn,
        "tn": tn,
        "fp": fp,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "duration_summary": duration_summary,
    }

    result_path = output_directory / "server_result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(
        f"[CentralizedRunner] Popper 4: {'solution found' if solution_found else 'no complete solution'} "
        f"in {total_time:.2f}s ({stats.total_programs} programs tested). "
        f"Result written to {result_path}"
    )


if __name__ == "__main__":
    main()

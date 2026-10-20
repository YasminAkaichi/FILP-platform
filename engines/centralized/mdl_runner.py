"""
Centralized (non-federated) MaxSynth / noisy-MDL run.

This wires in the 4th FILP learning approach: "Learning MDL Logic
Programs From Noisy Data" (Hocquette, Niskanen, Jarvisalo & Cropper,
arXiv:2308.09393). The vendored engine lives at symbolic/Popper-v3 —
its generate/test/COMBINE/constrain loop (loop.py + combine_mdl.py +
maxsat.py) extends Popper's own generate-test-constrain loop with a
MaxSAT-based "combine" stage (via pysat's RC2 solver) that merges small
"promising programs" into a single program minimizing the MDL cost
function cost(h) = size(h) + fn(h) + fp(h), rather than requiring a
program to perfectly separate positive and negative examples. That's
what makes it noise-tolerant where plain Popper 1.1.0 (popper-core,
used by the "centralized" / "popper" learner) is not.

The inner package was renamed from `popper` to `popper_mdl` (see
symbolic/Popper-v3/popper_mdl/) purely to avoid a Python import
collision with popper-core's own `popper` package, which is also on
sys.path and used by engines.centralized.runner for the non-noisy
centralized approach. All of popper_mdl's internal imports are
relative (`from . util import ...`), so the rename is cosmetic and
doesn't change its behaviour.

Run as its own subprocess (mirrors engines.centralized.runner, the
plain-Popper equivalent) so core/launcher.py can bound it with
subprocess.run(..., timeout=...) — this engine's timeout is also
signal.alarm()-based internally, which only works in a process's main
thread; Streamlit runs each page in a worker thread, hence the
subprocess boundary.

Writes a single JSON result file to --output-dir/server_result.json,
in the same shape core/launcher.py already expects for the other
approaches' server_result.json — plus two MDL-specific extra fields
(program_size, mdl_cost) that aren't part of the shared ServerResult
schema yet, but are kept in the raw JSON for a future UI addition.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
POPPER_MDL_PATH = PROJECT_ROOT / "symbolic" / "Popper-v3"

if str(POPPER_MDL_PATH) not in sys.path:
    sys.path.insert(0, str(POPPER_MDL_PATH))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Centralized (non-federated) noisy-MDL (MaxSynth) run"
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to the dataset directory (exs.pl / bk.pl / bias.pl)",
    )
    parser.add_argument(
        "--timeout", type=float, default=60.0, help="Max search time in seconds"
    )
    parser.add_argument(
        "--output-dir", required=True, help="Directory to write server_result.json into"
    )
    args = parser.parse_args()

    dataset_directory = Path(args.dataset)
    output_directory = Path(args.output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)

    from popper_mdl.util import Settings, format_prog, order_prog
    from popper_mdl.loop import learn_solution

    settings = Settings(
        bias_file=str(dataset_directory / "bias.pl"),
        ex_file=str(dataset_directory / "exs.pl"),
        bk_file=str(dataset_directory / "bk.pl"),
        timeout=args.timeout,
        noisy=True,
    )

    # "Stop" button: pressing it makes Popper-v3 return its best program so
    # far, exactly as its own timeout would (see stop_support.py).
    from engines.centralized.stop_support import install_stop_watcher, search_running

    install_stop_watcher(output_directory)

    start_time = time.perf_counter()
    with search_running():
        program, score, stats = learn_solution(settings)
    total_time = time.perf_counter() - start_time

    solution_found = program is not None

    if score is not None:
        tp, fn, tn, fp, program_size = score
    else:
        tp = fn = tn = fp = program_size = 0

    mdl_cost = program_size + fn + fp

    solution_code = (
        format_prog(order_prog(program)) if solution_found else None
    )

    total_predictions = tp + fn + tn + fp
    accuracy = (tp + tn) / total_predictions if total_predictions else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    # Same per-stage timing breakdown popper-core's Stats exposes
    # (generate / ground / test / add, etc.) — popper_mdl's Stats class
    # has the same duration_summary() shape.
    try:
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
    except Exception:
        duration_summary = []

    result = {
        "solution": solution_code,
        "solution_found": solution_found,
        "total_time": total_time,
        "startup_time": 0.0,
        "learning_time": total_time,
        "popper_time": total_time,
        "federation_time": 0.0,
        "federation_ratio": 0.0,
        "number_of_rounds": 1,
        "number_of_programs": getattr(stats, "total_programs", 0),
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
        # MDL-specific, not part of the shared ServerResult schema yet:
        "program_size": program_size,
        "mdl_cost": mdl_cost,
        "noisy": True,
    }

    result_path = output_directory / "server_result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(
        f"[CentralizedMdlRunner] {'Solution found' if solution_found else 'No solution'} "
        f"in {total_time:.2f}s (size={program_size}, MDL cost={mdl_cost}, "
        f"{getattr(stats, 'total_programs', 0)} programs tested). "
        f"Result written to {result_path}"
    )


if __name__ == "__main__":
    main()

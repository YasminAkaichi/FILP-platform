"""
Centralized (non-federated) Andante run.

This is the real, non-demo counterpart of the "Progol" option in
Try & Learn: Andante is a Progol-style ILP system (mode declarations,
determinations, inverse-entailment-style induction) that is already
vendored and proven in this codebase — Learning by Consensus has used
it as one of its two local learners since before this file existed
(engines/consensus/learners/andante.py).

Rather than reimplementing Andante plumbing, this module reuses the
exact building blocks Consensus already relies on:
  - partitioning.popper_to_andante.convert_popper_to_andante
    (translates the Popper bias.pl/bk.pl/exs.pl trio into Andante's
    single-file .pl format)
  - engines.consensus.learners.andante.AndanteConsensusLearner
    (wraps AndanteProgram.build_from(...) + .induce(...) + .predict(...))
  - engines.consensus.evaluator.read_andante_labels / evaluate_predictions
    (ground truth + tp/fn/tn/fp/accuracy/precision/recall/f1)

--dataset accepts two kinds of input:
  - a .pl file: a native, hand-written Andante example (mode
    declarations + background knowledge + examples, all in one file),
    such as the ones under datasets/andante/ (e.g. family.pl, copied
    from Andante's own bundled example at
    symbolic/andante/jupyter-notebooks/Examples/family.pl) — used as-is.
  - a directory: a Popper-format dataset (bias.pl/bk.pl/exs.pl), which
    gets auto-converted to Andante's single-file format first.

Run as its own subprocess (mirrors engines.centralized.runner, the
Popper equivalent) so core/launcher.py can bound it with
subprocess.run(..., timeout=...) — Andante's induce() has no built-in
timeout of its own, so the subprocess boundary is what keeps a
pathological run from hanging the Streamlit app.

Writes a single JSON result file to --output-dir/server_result.json,
in the same shape core/launcher.py already expects for other
approaches' server_result.json.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from engines.consensus.learners.andante import AndanteConsensusLearner
from engines.consensus.evaluator import evaluate_predictions, read_andante_labels
from partitioning.popper_to_andante import convert_popper_to_andante


def main() -> None:
    parser = argparse.ArgumentParser(description="Centralized (non-federated) Andante run")
    parser.add_argument("--dataset", required=True, help="Path to either a native Andante .pl file, or a Popper-format dataset directory (exs.pl / bk.pl / bias.pl) to convert")
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Informational only — the caller (core/launcher.py) enforces this as a subprocess timeout",
    )
    parser.add_argument("--output-dir", required=True, help="Directory to write server_result.json into")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_directory = Path(args.output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)

    if dataset_path.is_file():
        # A native, hand-written Andante file — use it as-is.
        andante_dataset_file = dataset_path
    elif dataset_path.is_dir():
        # A Popper-format dataset directory: Andante doesn't read
        # bias/bk/exs directly, so convert it to Andante's single-file
        # format first — the same converter Learning by Consensus uses.
        andante_dataset_file = output_directory / "andante_dataset.pl"
        convert_popper_to_andante(dataset_path, andante_dataset_file)
    else:
        raise FileNotFoundError(f"Andante dataset not found: {dataset_path}")

    start_time = time.perf_counter()

    learner = AndanteConsensusLearner(andante_dataset_file)
    hypothesis, _, _ = learner.learn()
    solution_found = bool(hypothesis)

    # Self-test on the same examples used for training. This matches how
    # the centralized Popper run is evaluated: there is no held-out test
    # set for a single, non-federated run, so the confusion matrix is
    # computed against the training examples in both cases.
    predictions = learner.predict(hypothesis, andante_dataset_file)
    labels = read_andante_labels(andante_dataset_file)
    metrics = evaluate_predictions(labels, predictions)

    total_time = time.perf_counter() - start_time

    result = {
        "solution": "\n".join(hypothesis) if hypothesis else None,
        "solution_found": solution_found,
        "total_time": total_time,
        "startup_time": 0.0,
        "learning_time": total_time,
        "popper_time": 0.0,
        "federation_time": 0.0,
        "federation_ratio": 0.0,
        "number_of_rounds": 1,
        # Andante doesn't enumerate candidate programs the way Popper's
        # generate-test-constrain loop does, so this counts learned
        # clauses instead of programs searched.
        "number_of_programs": len(hypothesis),
        "final_score": float(metrics["tp"] + metrics["tn"]),
        "tp": metrics["tp"],
        "fn": metrics["fn"],
        "tn": metrics["tn"],
        "fp": metrics["fp"],
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        # No per-stage timing breakdown for Andante (unlike Popper's
        # generate/ground/test/add stats) — left empty so the UI can
        # skip that section for this system.
        "duration_summary": [],
    }

    result_path = output_directory / "server_result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(
        f"[CentralizedAndanteRunner] {'Solution found' if solution_found else 'No solution'} "
        f"in {total_time:.2f}s ({len(hypothesis)} clause(s) learned). "
        f"Result written to {result_path}"
    )


if __name__ == "__main__":
    main()

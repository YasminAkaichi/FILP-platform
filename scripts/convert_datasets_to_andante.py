"""
Batch-convert every eligible Popper-format dataset under datasets/ into
a native Andante .pl file under datasets/andante/, so it can be picked
up by the Andante dropdown in Try & Learn (see
apps/app_pages/02_Inductive_logic_programming.py::get_available_andante_datasets,
which lists every *.pl file directly inside datasets/andante/).

Reuses partitioning.popper_to_andante.convert_popper_to_andante (the
same converter Learning by Consensus already relies on for its own
Andante-format partitions) — this script does not reimplement any
conversion logic, it just applies it across every dataset directory in
one pass and reports which ones succeeded or failed.

A Popper dataset directory is eligible if it has bias.pl/bk.pl/exs.pl
AND its bias.pl declares direction(...) for every predicate used in a
head_pred/body_pred declaration — direction() is required by the
converter to build Andante mode declarations (+/-), and several of the
platform's datasets (trains1, trains2, trains1000, iggp-rps, at time of
writing) don't declare it, so conversion for those fails with a clear
ValueError rather than silently producing a broken file.

Usage
-----
    python -m scripts.convert_datasets_to_andante
    python -m scripts.convert_datasets_to_andante --dataset zendo1
    python -m scripts.convert_datasets_to_andante --overwrite

By default, existing files in datasets/andante/ are left untouched
(skipped) — pass --overwrite to regenerate them. Datasets known not to
converge with Andante's search within a reasonable budget (as of this
investigation: zendo, zendo1, synthesis-sorted — see
datasets/andante/_not_yet_converging/ for their already-converted, and
already known-to-parse-but-not-learn, .pl files) are still converted by
this script if requested; convergence is a property of the learner and
the dataset's structure, not of the conversion step, and is outside
this script's scope.

NOTE ON CONVERTED FILES THAT DO CONVERGE: a converted file that DOES
learn successfully may still need a larger search budget than Andante's
default (100 states) to actually find a solution — see
datasets/andante/trains.pl, which starts with
`set(max_search_states, 5000).`, a directive this script does NOT add
automatically since the right budget is dataset-specific and was found
empirically, not derived from any general rule.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from partitioning.popper_to_andante import convert_popper_to_andante  # noqa: E402

DATASETS_DIR = PROJECT_ROOT / "datasets"
ANDANTE_DIR = DATASETS_DIR / "andante"


# Datasets deliberately excluded from the default (no --dataset given)
# batch, because datasets/andante/<name>.pl already exists as a
# hand-curated NATIVE Andante file for them — not an auto-conversion of
# datasets/<name>/ (a same-named but DIFFERENT Popper-format dataset).
# Auto-converting over these would silently replace curated content
# with a lossy auto-conversion. Pass --dataset family --overwrite
# explicitly if you really want to regenerate one of these from its
# Popper counterpart.
NATIVE_ANDANTE_OVERRIDES = {"family"}


def get_convertible_dataset_names() -> list[str]:
    """Popper-format dataset directories eligible for conversion —
    same filtering logic as
    apps/app_pages/02_Inductive_logic_programming.py::get_available_datasets,
    minus datasets that are already native-Andante-only (no bias/bk/exs),
    minus NATIVE_ANDANTE_OVERRIDES (see above)."""
    if not DATASETS_DIR.is_dir():
        return []
    return sorted(
        directory.name
        for directory in DATASETS_DIR.iterdir()
        if directory.is_dir()
        and directory.name not in ("generated", "andante")
        and directory.name not in NATIVE_ANDANTE_OVERRIDES
        and "_part" not in directory.name
        and (directory / "exs.pl").is_file()
        and (directory / "bk.pl").is_file()
        and (directory / "bias.pl").is_file()
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch-convert Popper datasets to native Andante .pl files"
    )
    parser.add_argument(
        "--dataset",
        action="append",
        default=None,
        help="Convert only this dataset (repeatable). Default: all eligible datasets.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files in datasets/andante/ (default: skip them).",
    )
    args = parser.parse_args()

    ANDANTE_DIR.mkdir(parents=True, exist_ok=True)

    names = args.dataset if args.dataset else get_convertible_dataset_names()
    if not names:
        print("No convertible datasets found.")
        return

    succeeded: list[str] = []
    failed: list[tuple[str, str]] = []
    skipped: list[str] = []

    for name in names:
        source_dir = DATASETS_DIR / name
        output_file = ANDANTE_DIR / f"{name}.pl"

        if output_file.is_file() and not args.overwrite:
            skipped.append(name)
            continue

        try:
            convert_popper_to_andante(source_dir, output_file)
            succeeded.append(name)
        except Exception as exc:  # noqa: BLE001 — report every failure, keep going
            failed.append((name, f"{type(exc).__name__}: {exc}"))

    print(f"Converted: {len(succeeded)}")
    for name in succeeded:
        print(f"  OK    {name} -> {ANDANTE_DIR / f'{name}.pl'}")

    if skipped:
        print(f"Skipped (already exists, use --overwrite to regenerate): {len(skipped)}")
        for name in skipped:
            print(f"  SKIP  {name}")

    if failed:
        print(f"Failed: {len(failed)}")
        for name, reason in failed:
            print(f"  FAIL  {name}: {reason}")


if __name__ == "__main__":
    main()

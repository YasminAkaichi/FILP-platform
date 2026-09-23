"""Isolated Popper-v4 trainer for Consensus.

Each invocation runs Popper in a fresh Python/SWI-Prolog process,
preventing the Prolog state of one client from leaking into another.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from popper.loop import learn_solution
from popper.util import Settings, format_rule


def train(
    dataset_path: Path,
    timeout: int = 600,
    debug: bool = False,
    show_stats: bool = False,
) -> dict:

    dataset_path = dataset_path.resolve()

    required_files = ("bias.pl", "bk.pl", "exs.pl")

    missing = [
        filename
        for filename in required_files
        if not (dataset_path / filename).is_file()
    ]

    if missing:
        raise FileNotFoundError(
            f"Invalid Popper dataset {dataset_path}. "
            f"Missing: {', '.join(missing)}"
        )

    settings = Settings(
        kbpath=str(dataset_path),
        cmd_line=False,
        timeout=timeout,
        show_stats=show_stats,
        debug=debug,
    )

    program, score, stats = learn_solution(settings)

    if program is None:
        hypothesis = []
    else:
        hypothesis = [
            format_rule(rule)
            for rule in program
        ]

    return {
        "hypothesis": hypothesis,
        "score": list(score) if score is not None else None,
    }


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        required=True,
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
    )

    args = parser.parse_args()

    result = train(
        dataset_path=Path(args.dataset),
        timeout=args.timeout,
    )

    # IMPORTANT:
    # stdout must contain only machine-readable JSON.
    print(json.dumps(result))


if __name__ == "__main__":
    main()
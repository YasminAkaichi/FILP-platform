"""Isolated Popper-v4 predictor for Consensus.

This module is executed in a fresh Python process so that the Prolog
state used during training cannot leak into evaluation.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import janus_swi as janus


def read_examples(
    exs_file: Path,
) -> tuple[list[str], str]:

    examples: list[str] = []
    predicate = None

    pattern = re.compile(
        r"^(pos|neg)\((\w+)\(([^)]+)\)\)\.$"
    )

    for raw_line in exs_file.read_text(
        encoding="utf-8"
    ).splitlines():

        line = raw_line.strip()

        if not line or line.startswith("%"):
            continue

        match = pattern.match(line)

        if not match:
            raise ValueError(
                f"Unsupported example: {line}"
            )

        _, current_predicate, example_id = (
            match.groups()
        )

        if predicate is None:
            predicate = current_predicate

        elif predicate != current_predicate:
            raise ValueError(
                "Multiple target predicates found."
            )

        examples.append(example_id)

    if predicate is None:
        raise ValueError(
            f"No examples found in {exs_file}"
        )

    return examples, predicate


def predict(
    hypothesis: list[str],
    test_dataset: Path,
) -> dict[str, bool]:

    exs_file = test_dataset / "exs.pl"
    bk_file = test_dataset / "bk.pl"

    examples, predicate = read_examples(exs_file)

    # Fresh process:
    # only TEST background knowledge is loaded.
    janus.consult(str(bk_file))

    rules = []

    for rule in hypothesis:

        rule = rule.strip()

        if not rule:
            continue

        if not rule.endswith("."):
            rule += "."

        rules.append(rule)

    program = (
        f":- dynamic {predicate}/1.\n"
        + "\n".join(rules)
    )

    janus.consult(
        "consensus_hypothesis",
        program,
    )

    predictions = {}

    for example_id in examples:

        query = f"{predicate}({example_id})"

        result = janus.query_once(query)

        predictions[example_id] = bool(
            result.get("truth", False)
        )

    return predictions


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--test-dataset",
        required=True,
    )

    parser.add_argument(
        "--hypothesis-file",
        required=True,
    )

    args = parser.parse_args()

    hypothesis = json.loads(
        Path(args.hypothesis_file).read_text(
            encoding="utf-8"
        )
    )

    predictions = predict(
        hypothesis=hypothesis,
        test_dataset=Path(args.test_dataset),
    )

    # stdout is intentionally machine-readable.
    print(json.dumps(predictions))


if __name__ == "__main__":
    main()
from __future__ import annotations

import re
from pathlib import Path

from partitioning.dataset import Dataset, Example, Fact, Rule


POSITIVE_PATTERN = re.compile(
    r"^\s*pos\((.+)\)\.\s*$"
)

NEGATIVE_PATTERN = re.compile(
    r"^\s*neg\((.+)\)\.\s*$"
)


def read_dataset(dataset_directory: Path) -> Dataset:
    dataset_directory = dataset_directory.resolve()

    if not dataset_directory.is_dir():
        raise FileNotFoundError(
            f"Dataset directory not found: {dataset_directory}"
        )

    examples_path = dataset_directory / "exs.pl"
    background_path = dataset_directory / "bk.pl"
    bias_path = dataset_directory / "bias.pl"

    for required_file in (
        examples_path,
        background_path,
        bias_path,
    ):
        if not required_file.is_file():
            raise FileNotFoundError(
                f"Required dataset file not found: {required_file}"
            )

    positive_examples, negative_examples = _read_examples(
        examples_path
    )

    facts, rules = _read_background_knowledge(
        background_path
    )

    bias = bias_path.read_text(
        encoding="utf-8"
    )

    return Dataset(
        name=dataset_directory.name,
        positive_examples=positive_examples,
        negative_examples=negative_examples,
        facts=facts,
        rules=rules,
        bias=bias,
    )


def _read_examples(
    examples_path: Path,
) -> tuple[list[Example], list[Example]]:
    positive_examples: list[Example] = []
    negative_examples: list[Example] = []

    for raw_line in examples_path.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if not line or line.startswith("%"):
            continue

        positive_match = POSITIVE_PATTERN.match(line)

        if positive_match:
            identifier = positive_match.group(1).strip()

            positive_examples.append(
                Example(
                    identifier=identifier,
                    positive=True,
                )
            )
            continue

        negative_match = NEGATIVE_PATTERN.match(line)

        if negative_match:
            identifier = negative_match.group(1).strip()

            negative_examples.append(
                Example(
                    identifier=identifier,
                    positive=False,
                )
            )
            continue

        raise ValueError(
            f"Unsupported example line in {examples_path}: {line}"
        )

    return positive_examples, negative_examples


def _read_background_knowledge(
    background_path: Path,
) -> tuple[list[Fact], list[Rule]]:
    statements = _split_prolog_statements(
        background_path.read_text(
            encoding="utf-8"
        )
    )

    facts: list[Fact] = []
    rules: list[Rule] = []

    for statement in statements:
        stripped = statement.strip()

        if not stripped:
            continue

        if ":-" in stripped:
            rules.append(
                Rule(text=stripped)
            )
            continue

        facts.append(
            Fact(
                text=stripped,
                example_identifier=_infer_example_identifier(
                    stripped
                ),
            )
        )

    return facts, rules


def _split_prolog_statements(
    content: str,
) -> list[str]:
    statements: list[str] = []
    current_lines: list[str] = []

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("%"):
            continue

        current_lines.append(raw_line)

        if line.endswith("."):
            statements.append(
                "\n".join(current_lines).strip()
            )
            current_lines = []

    if current_lines:
        raise ValueError(
            "The background knowledge contains an incomplete "
            "Prolog statement without a final period."
        )

    return statements


def _infer_example_identifier(
    fact: str,
) -> str | None:
    """
    Infer the Zendo-style example identifier.

    Examples:
        blue(p10_1).             -> "10"
        contact(p10_0, p10_3).  -> "10"

    Facts without an indexed term return None and are considered shared.
    """
    match = re.search(
        r"\bp(\d+)_\d+\b",
        fact,
    )

    if not match:
        return None

    return match.group(1)
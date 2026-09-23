"""Andante adapter for the Consensus engine.

The learned hypothesis is converted to the canonical Consensus
representation: one string per rule.
"""

from pathlib import Path
from typing import Any

from andante.program import AndanteProgram


class AndanteConsensusLearner:
    """Local Andante learner used by Learning by Consensus."""

    def __init__(self, dataset_path: str | Path) -> None:
        self.dataset_path = Path(dataset_path).resolve()

        if not self.dataset_path.is_file():
            raise FileNotFoundError(
                f"Andante dataset not found: {self.dataset_path}"
            )

        self.ilp: Any = None
        self.raw_hypothesis: Any = None

    def learn(self) -> tuple[list[str], None, None]:
        """Learn one local hypothesis with Andante."""

        self.ilp = AndanteProgram.build_from(
            str(self.dataset_path)
        )

        self.raw_hypothesis = self.ilp.induce(
            update_knowledge=True,
            logging=True,
            verbose=1,
        )

        if not self.raw_hypothesis:
            return [], None, None

        hypothesis = [
            str(rule).strip()
            for rule in self.raw_hypothesis
            if str(rule).strip()
        ]

        return hypothesis, None, None
    def predict(
    self,
    hypothesis: list[str],
    test_dataset: str | Path,
) -> dict[str, bool]:
        """Evaluate a learned hypothesis on an Andante test dataset."""

        test_dataset = Path(test_dataset).resolve()

        if not test_dataset.is_file():
            raise FileNotFoundError(
                f"Andante test dataset not found: {test_dataset}"
            )

        # Load the common test dataset.
        test_program = AndanteProgram.build_from(
            str(test_dataset)
        )

        # Add the learned hypothesis to the test background knowledge.
        #for rule in hypothesis:
        #    test_program.add_background_knowledge_from_text(
        #        rule
        #    )

        if hypothesis:
            hypothesis_text = "\n".join(hypothesis)

            background_text = (
                ":- begin_bg.\n"
                f"{hypothesis_text}\n"
                ":- end_bg."
            )

            test_program.add_background_knowledge_from_text(
                background_text
            )

        predictions: dict[str, bool] = {}

        # Evaluate the examples explicitly contained in the test set.
        for label in ("pos", "neg"):
            for example in test_program.examples[label]:

                # An example is represented as a bodyless Clause.
                target = example.head

                predicted_positive = test_program.solver.succeeds_on(
                    target,
                    test_program.knowledge,
                )

                example_id = (
                repr(target)
                .replace(", ", ",")
                )

                predictions[example_id] = bool(
                    predicted_positive
                )

        return predictions
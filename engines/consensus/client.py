"""Flower client for Learning by Consensus.

Each client:
1. learns one local symbolic hypothesis H_i;
2. serializes H_i and sends it to the server;
3. receives the collection of hypotheses learned by all clients;
4. later evaluates the ensemble through majority voting.

The local learner can be Popper-v4 or Andante.

how to run with popper :
PYTHONPATH="$PWD/symbolic/popper-v4:$PWD" \
python -m engines.consensus.client \
  --client-id 1 \
  --learner popper \
  --dataset datasets/generated/zendo1/consensus_iid_2_seed_42/train/zendo1_part1 \
  --test-dataset datasets/generated/zendo1/consensus_iid_2_seed_42/test \
  --server-address 127.0.0.1:8080


"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import flwr as fl
import numpy as np

from engines.consensus.learners.andante import AndanteConsensusLearner
from engines.consensus.aggregation import majority_vote
from engines.consensus.evaluator import (
    read_labels,
    read_andante_labels,
    evaluate_predictions,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def encode_json(payload: Any) -> list[np.ndarray]:
    """Encode a JSON-compatible object as Flower parameters."""
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return [np.frombuffer(raw, dtype=np.uint8).copy()]


def decode_json(parameters: list[np.ndarray]) -> Any:
    """Decode parameters produced by encode_json."""
    if not parameters:
        return None

    array = parameters[0]

    if array.size == 0:
        return None

    raw = array.astype(np.uint8, copy=False).tobytes()
    return json.loads(raw.decode("utf-8"))


# ---------------------------------------------------------------------------
# Learner factory
# ---------------------------------------------------------------------------

def build_learner(
    learner_name: str,
    dataset_path: Path,
    timeout: int,
):
    """Create the requested local ILP learner."""

    if learner_name == "popper":
        # Imported lazily on purpose.
        #
        # Consensus-Popper must be launched with symbolic/popper-v4
        # taking priority on PYTHONPATH. We do not want importing this
        # module to accidentally load popper-core.
        from engines.consensus.learners.popper import PopperConsensusLearner

        return PopperConsensusLearner(
            dataset_path=dataset_path,
            timeout=timeout,
        )

    if learner_name == "andante":
        return AndanteConsensusLearner(
            dataset_path=dataset_path,
        )

    raise ValueError(f"Unknown Consensus learner: {learner_name}")


# ---------------------------------------------------------------------------
# Flower client
# ---------------------------------------------------------------------------

class ConsensusClient(fl.client.NumPyClient):
    """Client participating in Learning by Consensus."""

    def __init__(
    self,
    client_id: str,
    learner_name: str,
    dataset_path: str | Path,
    test_dataset: str | Path,
    timeout: int = 600,
) -> None:

        self.client_id = str(client_id)
        self.learner_name = learner_name.lower()

        self.dataset_path = Path(
            dataset_path
        ).resolve()

        self.test_dataset = Path(
            test_dataset
        ).resolve()

        self.learner = build_learner(
            learner_name=self.learner_name,
            dataset_path=self.dataset_path,
            timeout=timeout,
        )

        self.local_hypothesis: list[str] = []
        self.received_hypotheses: list[list[str]] = []

    def get_parameters(self, config):
        """Return the current local hypothesis."""
        return encode_json(
            {
                "type": "local_hypothesis",
                "client_id": self.client_id,
                "learner": self.learner_name,
                "hypothesis": self.local_hypothesis,
            }
        )

    def set_parameters(self, parameters):
        """Receive the hypothesis ensemble from the server."""
        payload = decode_json(parameters)

        if not payload:
            self.received_hypotheses = []
            return

        if payload.get("type") != "hypothesis_ensemble":
            # Initial Flower parameters can be empty or unrelated to the
            # final ensemble. There is nothing to evaluate yet.
            self.received_hypotheses = []
            return

        hypotheses = payload.get("hypotheses", [])

        #self.received_hypotheses = [
         #   item["hypothesis"]
          #  for item in hypotheses
           # if item.get("hypothesis")
        #]
        self.received_hypotheses = [
            item.get("hypothesis", [])
            for item in hypotheses
        ]

        log.info(
            "Client %s received %d hypotheses",
            self.client_id,
            len(self.received_hypotheses),
        )

    def fit(self, parameters, config):
        """Learn one local hypothesis H_i."""

        log.info(
            "Client %s learning with %s on %s",
            self.client_id,
            self.learner_name,
            self.dataset_path,
        )

        hypothesis, score, stats = self.learner.learn()
        self.local_hypothesis = hypothesis

        log.info(
            "Client %s learned %d rules",
            self.client_id,
            len(self.local_hypothesis),
        )

        payload = {
            "type": "local_hypothesis",
            "client_id": self.client_id,
            "learner": self.learner_name,
            "hypothesis": self.local_hypothesis,
        }

        # Flower's num_examples is normally used for weighted aggregation.
        # Consensus does NOT weight hypotheses by the number of rules.
        # The server will treat every client hypothesis as one voter.
        num_examples = 1

        metrics = {
            "client_id": self.client_id,
            "learner": self.learner_name,
            "n_rules": len(self.local_hypothesis),
        }

        return encode_json(payload), num_examples, metrics
    

    def evaluate(self, parameters, config):
        """Evaluate the Consensus ensemble on the common global test set."""

        # Receive [H1, H2, ..., Hk] from the server.
        self.set_parameters(parameters)

        if not self.received_hypotheses:
            raise RuntimeError(
                "Consensus evaluation received no hypotheses."
            )

        print(
            f"\n=== CLIENT {self.client_id} "
            "CONSENSUS EVALUATION ==="
        )

        print(
            f"Received hypotheses: "
            f"{len(self.received_hypotheses)}"
        )

        # --------------------------------------------------------
        # 1. Each hypothesis votes on the SAME global test
        # --------------------------------------------------------

        hypothesis_predictions = []

        for index, hypothesis in enumerate(
            self.received_hypotheses,
            start=1,
        ):
            predictions = self.learner.predict(
                hypothesis,
                self.test_dataset,
            )

            hypothesis_predictions.append(
                predictions
            )

            positive_predictions = sum(
                bool(value)
                for value in predictions.values()
            )

            print(
                f"H{index}: "
                f"{positive_predictions}/"
                f"{len(predictions)} "
                "positive predictions"
            )

        # --------------------------------------------------------
        # 2. Strict majority
        # --------------------------------------------------------

        consensus_predictions = majority_vote(
            hypothesis_predictions
        )

        # --------------------------------------------------------
        # 3. Ground truth
        # --------------------------------------------------------

        if self.learner_name == "popper":
            labels = read_labels(
                self.test_dataset / "exs.pl"
            )

        elif self.learner_name == "andante":
            labels = read_andante_labels(
                self.test_dataset
            )

        else:
            raise ValueError(
                f"Unsupported learner: "
                f"{self.learner_name}"
            )

        # --------------------------------------------------------
        # 4. Consensus metrics
        # --------------------------------------------------------

        result = evaluate_predictions(
            labels,
            consensus_predictions,
        )

        # --------------------------------------------------------
        # 5. Detailed per-example prediction traces
        # --------------------------------------------------------

        vote_traces = []

        number_of_voters = len(
            hypothesis_predictions
        )

        required_majority = (
            number_of_voters // 2 + 1
        )

        print("\nConsensus votes:")

        for example_id, true_label in labels.items():

            hypothesis_votes = []

            # Individual prediction of H1, H2, ..., Hk
            for index, predictions in enumerate(
                hypothesis_predictions,
                start=1,
            ):
                local_prediction = bool(
                    predictions[example_id]
                )

                hypothesis_votes.append(
                    {
                        "hypothesis": f"H{index}",
                        "prediction": (
                            "POS"
                            if local_prediction
                            else "NEG"
                        ),
                    }
                )

            # Number of hypotheses voting POS.
            positive_votes = sum(
                vote["prediction"] == "POS"
                for vote in hypothesis_votes
            )

            consensus_prediction = bool(
                consensus_predictions[example_id]
            )

            true_label_name = (
                "POS"
                if bool(true_label)
                else "NEG"
            )

            prediction_name = (
                "POS"
                if consensus_prediction
                else "NEG"
            )

            # Store all information about this prediction.
            trace = {
                "example_id": example_id,
                "true_label": true_label_name,
                "votes": hypothesis_votes,
                "positive_votes": positive_votes,
                "number_of_voters": number_of_voters,
                "required_majority": required_majority,
                "prediction": prediction_name,
                "correct": (
                    consensus_prediction
                    == bool(true_label)
                ),
            }

            vote_traces.append(trace)

            # Human-readable terminal output.
            vote_details = " | ".join(
                f"{vote['hypothesis']}="
                f"{vote['prediction']}"
                for vote in hypothesis_votes
            )

            print(
                f"Example {example_id} | "
                f"true={true_label_name} | "
                f"{vote_details} | "
                f"votes={positive_votes}/"
                f"{number_of_voters} | "
                f"required={required_majority} | "
                f"prediction={prediction_name} | "
                f"correct={trace['correct']}"
            )

        # --------------------------------------------------------
        # 6. Print final Consensus metrics
        # --------------------------------------------------------

        print("\nConsensus metrics:")

        for name, value in result.items():
            print(f"  {name}: {value}")

        # --------------------------------------------------------
        # 7. Send metrics + prediction traces to Flower server
        # --------------------------------------------------------

        # Flower metrics must contain scalar values.
        # vote_traces is therefore serialized as a JSON string.
        metrics = {
            "client_id": self.client_id,
            "learner": self.learner_name,
            "n_hypotheses": len(
                self.received_hypotheses
            ),
            "tp": int(result["tp"]),
            "tn": int(result["tn"]),
            "fp": int(result["fp"]),
            "fn": int(result["fn"]),
            "accuracy": float(
                result["accuracy"]
            ),
            "precision": float(
                result["precision"]
            ),
            "recall": float(
                result["recall"]
            ),
            "f1": float(
                result["f1"]
            ),
            "vote_traces": json.dumps(
                vote_traces,
                ensure_ascii=False,
            ),
        }

        # Flower loss is not meaningful for symbolic
        # majority-vote evaluation here.
        loss = 0.0

        num_examples = len(labels)

        return loss, num_examples, metrics
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Learning by Consensus Flower client"
    )

    parser.add_argument(
        "--client-id",
        required=True,
        help="Identifier of this client",
    )


    parser.add_argument(
        "--learner",
        required=True,
        choices=["popper", "andante"],
        help="Local ILP learner",
    )

    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to the local client dataset",
    )
    parser.add_argument(
    "--test-dataset",
    required=True,
    help="Path to the common global test dataset.",
    )
    parser.add_argument(
        "--server-address",
        default="127.0.0.1:8080",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Local learner timeout in seconds",
    )

    return parser.parse_args()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    args = parse_args()

    client = ConsensusClient(
    client_id=args.client_id,
    learner_name=args.learner,
    dataset_path=args.dataset,
    test_dataset=args.test_dataset,
    timeout=args.timeout,
)

    fl.client.start_numpy_client(
        server_address=args.server_address,
        client=client,
    )


if __name__ == "__main__":
    main()
from dataclasses import dataclass
from typing import Literal


Approach = Literal[
    "collaboration",
    "consensus",
    "coordination",
]

PartitionStrategy = Literal[
    "iid",
    "non_iid",
]

Learner = Literal[
    "popper",
    "andante",
]


@dataclass
class ExperimentConfig:
    approach: Approach
    dataset: str
    number_of_clients: int
    partition_strategy: PartitionStrategy
    timing_mode: str = "wall"
    learner: str = "popper"
    random_seed: int = 42
    rounds: int = 35000
    timeout: int = 600
    server_address: str = "localhost:8080"

    def validate(self) -> None:
        if self.number_of_clients < 1:
            raise ValueError(
                "The number of clients must be at least 1."
            )

        if not self.dataset.strip():
            raise ValueError(
                "A dataset must be specified."
            )

        if self.rounds < 1:
            raise ValueError(
                "The number of rounds must be at least 1."
            )

        if self.timeout < 1:
            raise ValueError(
                "The learner timeout must be at least 1 second."
            )

        if self.learner not in {
            "popper",
            "popper-v4",
            "andante",
        }:
            raise ValueError(
                f"Unsupported learner: {self.learner}"
            )

        if not self.server_address.strip():
            raise ValueError(
                "A server address must be specified."
            )
from dataclasses import dataclass
from typing import Literal


Approach = Literal[
    "collaboration",
    "coordination",
]

PartitionStrategy = Literal[
    "iid",
    "non_iid",
]


@dataclass
class ExperimentConfig:
    approach: Approach
    dataset: str
    number_of_clients: int
    partition_strategy: PartitionStrategy

    learner: str = "popper"
    random_seed: int = 42
    rounds: int = 35000
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

        if not self.server_address.strip():
            raise ValueError(
                "A server address must be specified."
            )
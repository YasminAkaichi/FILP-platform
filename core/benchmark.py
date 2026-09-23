from dataclasses import dataclass

from core.experiment import Approach, PartitionStrategy


@dataclass
class BenchmarkConfig:
    name: str
    approach: Approach
    dataset: str
    number_of_clients: int
    partition_strategy: PartitionStrategy
    number_of_runs: int = 6
    base_seed: int = 42
    learner: str = "popper"
    rounds: int = 35000
    timeout: int = 600
    timing_mode: str = "wall"
    server_address: str = "localhost:8080"

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "A benchmark name must be specified."
            )

        if self.number_of_runs < 1:
            raise ValueError(
                "The number of runs must be at least 1."
            )

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

        if self.timing_mode not in {"wall", "cpu"}:
            raise ValueError(
                "Timing mode must be either 'wall' or 'cpu'."
            )
        if not self.server_address.strip():
            raise ValueError(
                "A server address must be specified."
            )
        
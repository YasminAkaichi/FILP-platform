from core.experiment import ExperimentConfig
from core.launcher import ExperimentLauncher

config = ExperimentConfig(
    approach="coordination",
    dataset="zendo1",
    number_of_clients=10,
    partition_strategy="non_iid",
    random_seed=42,
    rounds=35000,
    server_address="localhost:8080",
)

launcher = ExperimentLauncher()
launcher.run(config)


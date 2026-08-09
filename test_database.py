from core.experiment import ExperimentConfig
from database.repository import ExperimentRepository

config = ExperimentConfig(
    approach="collaboration",
    dataset="zendo1",
    number_of_clients=3,
    partition_strategy="iid",
)

repo = ExperimentRepository()

experiment_id = repo.create_experiment(config)

print(experiment_id)

repo.complete_experiment(experiment_id)

print("Done.")
from __future__ import annotations

from core.benchmark import BenchmarkConfig
from core.experiment import ExperimentConfig
from core.launcher import ExperimentLauncher
from database.repository import ExperimentRepository


class BenchmarkLauncher:
    def run(self, config: BenchmarkConfig) -> int:
        config.validate()

        repository = ExperimentRepository()
        experiment_launcher = ExperimentLauncher()

        benchmark_id = repository.create_benchmark(config)

        print("\n========== STARTING BENCHMARK ==========")
        print(f"Benchmark ID      : {benchmark_id}")
        print(f"Name              : {config.name}")
        print(f"Approach          : {config.approach}")
        print(f"Dataset           : {config.dataset}")
        print(f"Clients           : {config.number_of_clients}")
        print(f"Partition strategy: {config.partition_strategy}")
        print(f"Runs              : {config.number_of_runs}")
        print(f"Base seed         : {config.base_seed}")
        print("========================================\n")

        try:
            for run_number in range(1, config.number_of_runs + 1):
                #random_seed = config.base_seed + run_number - 1
                random_seed = config.base_seed

                print(
                    f"\n========== BENCHMARK RUN "
                    f"{run_number}/{config.number_of_runs} =========="
                )
                print(f"Random seed: {random_seed}")

                experiment_config = ExperimentConfig(
                    approach=config.approach,
                    dataset=config.dataset,
                    number_of_clients=config.number_of_clients,
                    partition_strategy=config.partition_strategy,
                    learner=config.learner,
                    random_seed=random_seed,
                    rounds=config.rounds,
                    server_address=config.server_address,
                )

                experiment_id = experiment_launcher.run(
                    experiment_config
                )

                repository.add_benchmark_run(
                    benchmark_id=benchmark_id,
                    experiment_id=experiment_id,
                    run_number=run_number,
                    random_seed=random_seed,
                )

                print(
                    f"[Benchmark] Run {run_number}/"
                    f"{config.number_of_runs} completed. "
                    f"Experiment ID: {experiment_id}"
                )

            repository.complete_benchmark(benchmark_id)

            print(
                f"\n[Benchmark] Benchmark {benchmark_id} "
                "completed successfully."
            )

            return benchmark_id

        except Exception as error:
            repository.fail_benchmark(
                benchmark_id=benchmark_id,
                error_message=str(error),
            )

            print(
                f"\n[Benchmark] Benchmark {benchmark_id} "
                "saved as FAILED."
            )

            raise
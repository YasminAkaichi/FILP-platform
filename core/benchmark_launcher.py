from __future__ import annotations

from core.benchmark import BenchmarkConfig
from core.experiment import ExperimentConfig
from core.launcher import ExperimentLauncher
from core.run_control import RunControl, RunStopped
from database.repository import ExperimentRepository


class BenchmarkLauncher:
    def run(
        self,
        config: BenchmarkConfig,
        process_tracker: dict | None = None,
        control: RunControl | None = None,
    ) -> int:
        """
        control: optional RunControl for the "Stop" button. A stop lets the
        current run finish with the best result found so far and skips the
        remaining runs. Raises RunStopped if no run produced a result.
        """
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

        runs_done = 0

        try:
            for run_number in range(1, config.number_of_runs + 1):
                if control is not None and control.stop_requested:
                    print("[Benchmark] Stop requested: remaining runs skipped.")
                    break

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
                    timeout=config.timeout,
                    timing_mode=config.timing_mode,
                    server_address=config.server_address,
                )

                experiment_id = experiment_launcher.run(
                    experiment_config,
                    process_tracker=process_tracker,
                    control=control,
                )

                repository.add_benchmark_run(
                    benchmark_id=benchmark_id,
                    experiment_id=experiment_id,
                    run_number=run_number,
                    random_seed=random_seed,
                )
                runs_done += 1

                print(
                    f"[Benchmark] Run {run_number}/"
                    f"{config.number_of_runs} completed. "
                    f"Experiment ID: {experiment_id}"
                )

            if control is not None and control.stop_requested:
                if runs_done == 0:
                    raise RunStopped(benchmark_id)
                repository.complete_benchmark(
                    benchmark_id,
                    note=(
                        "Stopped by the user after "
                        f"{runs_done}/{config.number_of_runs} run(s)."
                    ),
                )
            else:
                repository.complete_benchmark(benchmark_id)

            print(
                f"\n[Benchmark] Benchmark {benchmark_id} "
                "completed successfully."
            )

            return benchmark_id

        except RunStopped:
            if runs_done > 0:
                # Earlier runs of this benchmark did produce results: keep
                # them, the stopped run is simply not counted.
                repository.complete_benchmark(
                    benchmark_id,
                    note=(
                        "Stopped by the user after "
                        f"{runs_done}/{config.number_of_runs} run(s)."
                    ),
                )
                print(
                    f"\n[Benchmark] Benchmark {benchmark_id} stopped after "
                    f"{runs_done} run(s); their results were kept."
                )
                return benchmark_id

            repository.stop_benchmark(
                benchmark_id,
                "Stopped by the user before any run produced a result.",
            )
            print(f"\n[Benchmark] Benchmark {benchmark_id} saved as STOPPED.")
            raise RunStopped(benchmark_id)

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
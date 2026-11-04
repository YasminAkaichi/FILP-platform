from __future__ import annotations

from core.benchmark import BenchmarkConfig
from core.experiment import ExperimentConfig
from core.launcher import ExperimentLauncher
from core.port_utils import find_free_port
from core.run_control import RunControl, RunStopped
from database.repository import ExperimentRepository
from database.schema import initialize_database
from database.connection import get_connection


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
        initialize_database()  # make sure the link columns exist

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

        # Hybrid evaluation (Coordination): a second benchmark holds the
        # centralized-testing runs, linked to this one by its name.
        central_benchmark_id = None
        if config.centralized_testing and config.approach in (
            "coordination",
            "collaboration",
        ):
            central_benchmark_id = repository.create_benchmark(
                BenchmarkConfig(
                    name=(
                        f"Centralized testing, whole {config.dataset} "
                        f"· same seed as #{benchmark_id}"
                    ),
                    approach=config.approach,
                    dataset=config.dataset,
                    number_of_clients=1,
                    partition_strategy="iid",
                    number_of_runs=config.number_of_runs,
                    base_seed=config.base_seed,
                    learner=config.learner,
                    rounds=config.rounds,
                    timeout=config.timeout,
                    timing_mode=config.timing_mode,
                    server_address=config.server_address,
                )
            )

        try:
            for run_number in range(1, config.number_of_runs + 1):
                if control is not None and control.stop_requested:
                    print("[Benchmark] Stop requested: remaining runs skipped.")
                    break

                #random_seed = config.base_seed + run_number - 1
                # Consensus experiments need independent splits per run
                # (mean +- std over seeds); other approaches keep the same
                # split so they stay comparable run to run.
                reference_experiment_id = None
                if config.reference_benchmark_id is not None:
                    # Centralized baseline: run i mirrors run i of the
                    # consensus benchmark (same dataset, seed, split).
                    with get_connection() as connection:
                        reference = connection.execute(
                            "SELECT experiment_id, random_seed FROM benchmark_runs "
                            "WHERE benchmark_id = ? AND run_number = ?",
                            (config.reference_benchmark_id, run_number),
                        ).fetchone()
                    if reference is None:
                        raise ValueError(
                            f"Consensus benchmark {config.reference_benchmark_id} "
                            f"has no run {run_number}."
                        )
                    reference_experiment_id = int(reference["experiment_id"])
                    random_seed = int(reference["random_seed"])
                elif config.approach == "consensus":
                    random_seed = config.base_seed + run_number - 1
                else:
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
                    reference_experiment_id=reference_experiment_id,
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

                # Hybrid evaluation, second search: the same Coordination
                # search, but ONE client holding the whole dataset tests the
                # programs (centralized testing). Run right after the
                # federated run, alone on the machine, so that both are
                # timed in the same conditions.
                if central_benchmark_id is not None and not (
                    control is not None and control.stop_requested
                ):
                    print(
                        f"[Benchmark] Run {run_number}: centralized "
                        "testing (1 client, whole dataset)..."
                    )
                    central_experiment_id = experiment_launcher.run(
                        ExperimentConfig(
                            approach=config.approach,
                            dataset=config.dataset,
                            number_of_clients=1,
                            partition_strategy="iid",
                            learner=config.learner,
                            random_seed=random_seed,
                            rounds=config.rounds,
                            timeout=config.timeout,
                            timing_mode=config.timing_mode,
                            # Fresh port: the federated server of this run
                            # may not have released its own yet.
                            server_address=f"localhost:{find_free_port()}",
                        ),
                        process_tracker=process_tracker,
                        control=control,
                    )
                    repository.add_benchmark_run(
                        benchmark_id=central_benchmark_id,
                        experiment_id=central_experiment_id,
                        run_number=run_number,
                        random_seed=random_seed,
                    )

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

            if central_benchmark_id is not None:
                repository.complete_benchmark(central_benchmark_id)

            print(
                f"\n[Benchmark] Benchmark {benchmark_id} "
                "completed successfully."
            )

            return benchmark_id

        except RunStopped:
            if central_benchmark_id is not None:
                if runs_done > 0:
                    repository.complete_benchmark(central_benchmark_id)
                else:
                    repository.stop_benchmark(
                        central_benchmark_id,
                        "Stopped by the user before any run produced a result.",
                    )
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
            if central_benchmark_id is not None:
                repository.fail_benchmark(
                    benchmark_id=central_benchmark_id,
                    error_message=str(error),
                )
            repository.fail_benchmark(
                benchmark_id=benchmark_id,
                error_message=str(error),
            )

            print(
                f"\n[Benchmark] Benchmark {benchmark_id} "
                "saved as FAILED."
            )

            raise
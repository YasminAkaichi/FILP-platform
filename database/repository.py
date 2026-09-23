from datetime import datetime

from database.connection import get_connection
from core.experiment import ExperimentConfig
from core.results import ClientResult, ServerResult, ConsensusResult
from core.benchmark import BenchmarkConfig
import json 

class ExperimentRepository:

    def create_experiment(self, config: ExperimentConfig) -> int:

        now = datetime.now().isoformat(timespec="seconds")

        with get_connection() as conn:

            cursor = conn.execute(
                """
                INSERT INTO experiments (
                    created_at,
                    started_at,
                    approach,
                    dataset,
                    number_of_clients,
                    partition_strategy,
                    learner,
                    random_seed,
                    rounds,
                    server_address,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    now,
                    config.approach,
                    config.dataset,
                    config.number_of_clients,
                    config.partition_strategy,
                    config.learner,
                    config.random_seed,
                    config.rounds,
                    config.server_address,
                    "RUNNING",
                ),
            )

            conn.commit()

            return cursor.lastrowid

    def complete_experiment(self, experiment_id: int):

        now = datetime.now().isoformat(timespec="seconds")

        with get_connection() as conn:

            conn.execute(
                """
                UPDATE experiments
                SET
                    completed_at = ?,
                    status = ?
                WHERE id = ?
                """,
                (
                    now,
                    "COMPLETED",
                    experiment_id,
                ),
            )

            conn.commit()
    
    def save_server_result(
    self,
    experiment_id: int,
    result: ServerResult,
    all_clients_accepted: bool,
) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO server_results (
                    experiment_id,
                    solution,
                    solution_found,
                    all_clients_accepted,
                    total_time_seconds,
                    startup_time_seconds,
                    learning_time_seconds,
                    popper_time_seconds,
                    federation_time_seconds,
                    federation_ratio,
                    number_of_rounds,
                    number_of_programs,
                    final_score,
                    tp,
                    fn,
                    tn,
                    fp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment_id,
                    result.solution,
                    int(result.solution_found),
                    int(all_clients_accepted),
                    result.total_time,
                    result.startup_time,
                    result.learning_time,
                    result.popper_time,
                    result.federation_time,
                    result.federation_ratio,
                    result.number_of_rounds,
                    result.number_of_programs,
                    result.final_score,
                    result.tp,
                    result.fn,
                    result.tn,
                    result.fp,
                ),
            )

            conn.commit()
    def save_client_result(
    self,
    experiment_id: int,
    result: ClientResult,
) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO client_results (
                    experiment_id,
                    client_id,
                    dataset_partition,
                    number_of_examples,
                    number_of_positive_examples,
                    number_of_negative_examples,
                    number_of_evaluations,
                    total_eval_wall_seconds,
                    total_eval_cpu_seconds,
                    average_eval_wall_seconds,
                    average_eval_cpu_seconds,
                    final_epsilon_positive,
                    final_epsilon_negative,
                    accepted_solution,
                    final_score,
                    tp,
                    fn,
                    tn,
                    fp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment_id,
                    result.client_id,
                    result.dataset_partition,
                    result.number_of_examples,
                    result.number_of_positive_examples,
                    result.number_of_negative_examples,
                    result.number_of_evaluations,
                    result.total_eval_wall,
                    result.total_eval_cpu,
                    result.average_eval_wall,
                    result.average_eval_cpu,
                    result.final_epsilon_positive,
                    result.final_epsilon_negative,
                    int(result.accepted_solution),
                    result.final_score,
                    result.tp,
                    result.fn,
                    result.tn,
                    result.fp,
                ),
            )

            conn.commit()
    
    def save_consensus_result(
        self,
        experiment_id: int,
        result: ConsensusResult,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO consensus_results (
                    experiment_id,
                    learner,
                    number_of_clients,
                    number_of_hypotheses,
                    hypotheses,
                    tp,
                    fn,
                    tn,
                    fp,
                    accuracy,
                    precision,
                    recall,
                    f1
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment_id,
                    result.learner,
                    result.number_of_clients,
                    result.number_of_hypotheses,
                    json.dumps(
                        result.hypotheses,
                        ensure_ascii=False,
                    ),
                    result.tp,
                    result.fn,
                    result.tn,
                    result.fp,
                    result.accuracy,
                    result.precision,
                    result.recall,
                    result.f1,
                ),
            )

            conn.commit()
    
    def fail_experiment(
        self,
        experiment_id: int,
        error_message: str,
    ):

        now = datetime.now().isoformat(timespec="seconds")

        with get_connection() as conn:

            conn.execute(
                """
                UPDATE experiments
                SET
                    completed_at = ?,
                    status = ?,
                    error_message = ?
                WHERE id = ?
                """,
                (
                    now,
                    "FAILED",
                    error_message,
                    experiment_id,
                ),
            )

            conn.commit()
    
    def create_benchmark(
    self,
    config: BenchmarkConfig,
) -> int:
        now = datetime.now().isoformat(timespec="seconds")

        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO benchmarks (
                    name,
                    created_at,
                    approach,
                    dataset,
                    number_of_clients,
                    partition_strategy,
                    number_of_runs,
                    base_seed,
                    learner,
                    rounds,
                    server_address,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    config.name,
                    now,
                    config.approach,
                    config.dataset,
                    config.number_of_clients,
                    config.partition_strategy,
                    config.number_of_runs,
                    config.base_seed,
                    config.learner,
                    config.rounds,
                    config.server_address,
                    "RUNNING",
                ),
            )

            conn.commit()

            if cursor.lastrowid is None:
                raise RuntimeError(
                    "The benchmark ID could not be created."
                )

            return int(cursor.lastrowid)


    def add_benchmark_run(
        self,
        benchmark_id: int,
        experiment_id: int,
        run_number: int,
        random_seed: int,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO benchmark_runs (
                    benchmark_id,
                    experiment_id,
                    run_number,
                    random_seed
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    benchmark_id,
                    experiment_id,
                    run_number,
                    random_seed,
                ),
            )

            conn.commit()


    def complete_benchmark(
        self,
        benchmark_id: int,
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")

        with get_connection() as conn:
            conn.execute(
                """
                UPDATE benchmarks
                SET
                    completed_at = ?,
                    status = ?
                WHERE id = ?
                """,
                (
                    now,
                    "COMPLETED",
                    benchmark_id,
                ),
            )

            conn.commit()


    def fail_benchmark(
        self,
        benchmark_id: int,
        error_message: str,
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")

        with get_connection() as conn:
            conn.execute(
                """
                UPDATE benchmarks
                SET
                    completed_at = ?,
                    status = ?,
                    error_message = ?
                WHERE id = ?
                """,
                (
                    now,
                    "FAILED",
                    error_message,
                    benchmark_id,
                ),
            )

            conn.commit()
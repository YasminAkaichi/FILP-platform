from core.benchmark_results import load_benchmark_summary
from database.connection import get_connection


def load_benchmark_metadata(benchmark_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                name,
                approach,
                dataset,
                number_of_clients,
                partition_strategy,
                number_of_runs,
                base_seed,
                learner,
                rounds,
                status
            FROM benchmarks
            WHERE id = ?
            """,
            (benchmark_id,),
        ).fetchone()

    if row is None:
        raise ValueError(
            f"Benchmark {benchmark_id} was not found."
        )

    return dict(row)


benchmark_id = 57

metadata = load_benchmark_metadata(benchmark_id)
summary = load_benchmark_summary(benchmark_id)

print("========== BENCHMARK CONFIGURATION ==========")
print(f"Benchmark ID : {metadata['id']}")
print(f"Name         : {metadata['name']}")
print(f"Approach     : {metadata['approach']}")
print(f"Dataset      : {metadata['dataset']}")
print(f"Clients      : {metadata['number_of_clients']}")
print(f"Partition    : {metadata['partition_strategy']}")
print(f"Runs         : {metadata['number_of_runs']}")
print(f"Base seed    : {metadata['base_seed']}")
print(f"Status       : {metadata['status']}")
print()

print("========== AGGREGATED RESULTS ==========")
print(f"Total time  : {summary.total_time.mean:.4f} ± "
      f"{summary.total_time.std:.4f}s")
print(
    f"Startup     : "
    f"{summary.startup_time.mean:.4f} ± "
    f"{summary.startup_time.std:.4f}s"
)

print(
    f"Learning    : "
    f"{summary.learning_time.mean:.4f} ± "
    f"{summary.learning_time.std:.4f}s"
)
print(f"Popper time : {summary.popper_time.mean:.4f} ± "
      f"{summary.popper_time.std:.4f}s")
print(f"Fed. time   : {summary.federation_time.mean:.4f} ± "
      f"{summary.federation_time.std:.4f}s")
print(f"Rounds      : {summary.number_of_rounds.mean:.2f} ± "
      f"{summary.number_of_rounds.std:.2f}")
print(f"Programs    : {summary.number_of_programs.mean:.2f} ± "
      f"{summary.number_of_programs.std:.2f}")
print(f"Final score : {summary.final_score.mean:.2f} ± "
      f"{summary.final_score.std:.2f}")
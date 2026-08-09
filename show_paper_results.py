from database.connection import get_connection
import statistics


def show_results(label, benchmark_ids):
    placeholders = ",".join("?" for _ in benchmark_ids)

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT
                b.id AS benchmark_id,
                b.name,
                e.id AS experiment_id,
                sr.learning_time_seconds
            FROM benchmarks b
            JOIN benchmark_runs br
                ON br.benchmark_id = b.id
            JOIN experiments e
                ON e.id = br.experiment_id
            JOIN server_results sr
                ON sr.experiment_id = e.id
            WHERE b.id IN ({placeholders})
              AND b.status = 'COMPLETED'
            ORDER BY b.id
            """,
            benchmark_ids,
        ).fetchall()

    values = [
        float(row["learning_time_seconds"])
        for row in rows
    ]

    print(f"\n========== {label} ==========")

    for i, row in enumerate(rows, 1):
        print(
            f"Run {i}: "
            f"{row['learning_time_seconds']:.4f}s "
            f"(benchmark {row['benchmark_id']}, "
            f"experiment {row['experiment_id']})"
        )

    mean = statistics.mean(values)
    std = statistics.stdev(values)

    print("--------------------------------")
    print(f"Runs   : {len(values)}")
    print(f"Mean   : {mean:.4f}s")
    print(f"Std    : {std:.4f}s")
    print(f"RESULT : {mean:.4f} ± {std:.4f}s")


show_results(
    "Trains2 — K=10",
    [29, 30, 31, 32, 33, 34],
)

show_results(
    "Zendo1 — K=2",
    [35, 36, 37, 38, 39, 40],
)
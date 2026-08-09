from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, stdev

from database.connection import get_connection


@dataclass
class MetricSummary:
    mean: float
    std: float
    minimum: float
    maximum: float


@dataclass
class BenchmarkSummary:
    benchmark_id: int
    number_of_runs: int
    total_time: MetricSummary
    startup_time: MetricSummary
    learning_time: MetricSummary
    popper_time: MetricSummary
    federation_time: MetricSummary
    federation_ratio: MetricSummary
    final_score: MetricSummary
    number_of_rounds: MetricSummary
    number_of_programs: MetricSummary


def _summarize(values: list[float]) -> MetricSummary:
    if not values:
        return MetricSummary(
            mean=0.0,
            std=0.0,
            minimum=0.0,
            maximum=0.0,
        )

    return MetricSummary(
        mean=float(mean(values)),
        std=float(stdev(values)) if len(values) > 1 else 0.0,
        minimum=float(min(values)),
        maximum=float(max(values)),
    )




def load_benchmark_summary(
    benchmark_id: int,
) -> BenchmarkSummary:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                sr.total_time_seconds,
                sr.startup_time_seconds,
                sr.learning_time_seconds,
                sr.popper_time_seconds,
                sr.federation_time_seconds,
                sr.federation_ratio,
                sr.final_score,
                sr.number_of_rounds,
                sr.number_of_programs
            FROM benchmark_runs AS br
            JOIN server_results AS sr
                ON sr.experiment_id = br.experiment_id
            WHERE br.benchmark_id = ?
            ORDER BY br.run_number
            """,
            (benchmark_id,),
        ).fetchall()

    if not rows:
        raise ValueError(
            f"No completed benchmark results found for benchmark {benchmark_id}."
        )

    return BenchmarkSummary(
        benchmark_id=benchmark_id,
        number_of_runs=len(rows),
        total_time=_summarize(
            [float(row["total_time_seconds"] or 0.0) for row in rows]
        ),
        startup_time=_summarize(
            [
                float(row["startup_time_seconds"] or 0.0)
                for row in rows
            ]
        ),
        learning_time=_summarize(
            [
                float(row["learning_time_seconds"] or 0.0)
                for row in rows
            ]
        ),
        popper_time=_summarize(
            [float(row["popper_time_seconds"] or 0.0) for row in rows]
        ),
        federation_time=_summarize(
            [float(row["federation_time_seconds"] or 0.0) for row in rows]
        ),
        federation_ratio=_summarize(
            [float(row["federation_ratio"] or 0.0) for row in rows]
        ),
        final_score=_summarize(
            [float(row["final_score"] or 0.0) for row in rows]
        ),
        number_of_rounds=_summarize(
            [float(row["number_of_rounds"] or 0.0) for row in rows]
        ),
        number_of_programs=_summarize(
            [float(row["number_of_programs"] or 0.0) for row in rows]
        ),
    )
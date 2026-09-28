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
    popper_core_time: MetricSummary
    client_eval_time: MetricSummary
    evaluate_phase_time: MetricSummary
    popper_time: MetricSummary
    federation_time: MetricSummary
    federation_ratio: MetricSummary
    final_score: MetricSummary
    number_of_rounds: MetricSummary
    number_of_programs: MetricSummary

@dataclass
class ConsensusBenchmarkSummary:
    benchmark_id: int
    number_of_runs: int

    accuracy: MetricSummary
    precision: MetricSummary
    recall: MetricSummary
    f1: MetricSummary

    tp: MetricSummary
    tn: MetricSummary
    fp: MetricSummary
    fn: MetricSummary

    number_of_hypotheses: MetricSummary

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


def load_consensus_benchmark_summary(
    benchmark_id: int,
) -> ConsensusBenchmarkSummary:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                cr.accuracy,
                cr.precision,
                cr.recall,
                cr.f1,
                cr.tp,
                cr.tn,
                cr.fp,
                cr.fn,
                cr.number_of_hypotheses
            FROM benchmark_runs AS br
            JOIN consensus_results AS cr
                ON cr.experiment_id = br.experiment_id
            WHERE br.benchmark_id = ?
            ORDER BY br.run_number
            """,
            (benchmark_id,),
        ).fetchall()

    if not rows:
        raise ValueError(
            f"No consensus results found for benchmark {benchmark_id}."
        )

    return ConsensusBenchmarkSummary(
        benchmark_id=benchmark_id,
        number_of_runs=len(rows),
        accuracy=_summarize(
            [float(row["accuracy"] or 0.0) for row in rows]
        ),
        precision=_summarize(
            [float(row["precision"] or 0.0) for row in rows]
        ),
        recall=_summarize(
            [float(row["recall"] or 0.0) for row in rows]
        ),
        f1=_summarize(
            [float(row["f1"] or 0.0) for row in rows]
        ),
        tp=_summarize(
            [float(row["tp"] or 0.0) for row in rows]
        ),
        tn=_summarize(
            [float(row["tn"] or 0.0) for row in rows]
        ),
        fp=_summarize(
            [float(row["fp"] or 0.0) for row in rows]
        ),
        fn=_summarize(
            [float(row["fn"] or 0.0) for row in rows]
        ),
        number_of_hypotheses=_summarize(
            [
                float(row["number_of_hypotheses"] or 0.0)
                for row in rows
            ]
        ),
    )

def load_benchmark_summary(
    benchmark_id: int,
) -> BenchmarkSummary:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                sr.experiment_id,
                sr.total_time_seconds,
                sr.startup_time_seconds,
                sr.learning_time_seconds,
                sr.popper_time_seconds,
                sr.federation_time_seconds,
                sr.federation_ratio,
                sr.final_score,
                sr.number_of_rounds,
                sr.number_of_programs,
                COALESCE(ce.client_eval_wall, 0.0) AS client_eval_wall,
                COALESCE(ce.evaluate_phase_wall, 0.0) AS evaluate_phase_wall
            FROM benchmark_runs AS br
            JOIN server_results AS sr
                ON sr.experiment_id = br.experiment_id
            LEFT JOIN (
                SELECT
                    experiment_id,
                    MAX(total_eval_wall_seconds) AS client_eval_wall,
                    MAX(total_evaluate_phase_wall_seconds) AS evaluate_phase_wall
                FROM client_results
                GROUP BY experiment_id
            ) AS ce
                ON ce.experiment_id = sr.experiment_id
            WHERE br.benchmark_id = ?
            ORDER BY br.run_number
            """,
            (benchmark_id,),
        ).fetchall()

    if not rows:
        raise ValueError(
            f"No completed benchmark results found for benchmark {benchmark_id}."
        )

    # `popper_time_seconds` (tCentralPopper) is timed strictly around the
    # server's own build/ground/add work between federated rounds, and
    # `federation_time_seconds` (tFedPopper) around `_send_and_wait`, i.e.
    # the whole round-trip during which each client evaluates the proposed
    # program against its local examples (see engines/collaboration/
    # strategy/fedpopper.py and engines/collaboration/client.py). That
    # client-side coverage testing is genuine Popper work, not federation
    # overhead — it's just been offloaded to the clients — so it's added
    # back into "Popper core" here and subtracted out of "federation" to
    # get a fair split between real search cost and pure communication/
    # aggregation overhead. Centralized/consensus runs have no
    # client_results rows, so client_eval_wall is 0 and both values are
    # unchanged from the raw server-side timers.
    #
    # MAX, not SUM, across clients: clients evaluate a given hypothesis
    # in parallel (separate processes/threads dispatched together each
    # round), so the server's wall-clock federation timer is bounded by
    # whichever client was slowest that round, not by the total compute
    # summed across all of them. Summing would subtract roughly
    # (number_of_clients)x too much from the raw federation time,
    # driving it toward — or below, silently clipped at — zero.
    #
    # evaluate_phase_wall: because fraction_evaluate=1.0, Flower runs a
    # SECOND, separate phase every round (configure_evaluate ->
    # client.evaluate()) that re-runs tester.test() on the same rules
    # fit() already tested. That call used to be completely untimed and
    # silently inflated "federation overhead" — on a search-heavy
    # dataset (trains1000) it accounted for roughly 60% of what looked
    # like pure communication cost. It's now measured directly
    # (total_evaluate_phase_wall_seconds) and subtracted out here too,
    # the same way client_eval_wall is.
    raw_popper_times: list[float] = []
    client_eval_times: list[float] = []
    evaluate_phase_times: list[float] = []
    true_popper_times: list[float] = []
    true_federation_times: list[float] = []
    true_federation_ratios: list[float] = []

    for row in rows:
        client_eval = float(row["client_eval_wall"] or 0.0)
        evaluate_phase = float(row["evaluate_phase_wall"] or 0.0)
        raw_popper = float(row["popper_time_seconds"] or 0.0)
        raw_federation = float(row["federation_time_seconds"] or 0.0)
        total_time = float(row["total_time_seconds"] or 0.0)

        true_popper = raw_popper + client_eval
        true_federation = max(
            raw_federation - client_eval - evaluate_phase, 0.0
        )

        raw_popper_times.append(raw_popper)
        client_eval_times.append(client_eval)
        evaluate_phase_times.append(evaluate_phase)
        true_popper_times.append(true_popper)
        true_federation_times.append(true_federation)
        true_federation_ratios.append(true_federation / total_time if total_time > 0 else 0.0)

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
        popper_core_time=_summarize(raw_popper_times),
        client_eval_time=_summarize(client_eval_times),
        evaluate_phase_time=_summarize(evaluate_phase_times),
        popper_time=_summarize(true_popper_times),
        federation_time=_summarize(true_federation_times),
        federation_ratio=_summarize(true_federation_ratios),
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

def load_consensus_benchmark_runs(
    benchmark_id: int,
) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                br.run_number,
                br.random_seed,
                br.experiment_id,
                e.status,
                cr.learner,
                cr.number_of_clients,
                cr.number_of_hypotheses,
                cr.hypotheses,
                cr.tp,
                cr.fn,
                cr.tn,
                cr.fp,
                cr.accuracy,
                cr.precision,
                cr.recall,
                cr.f1
            FROM benchmark_runs AS br
            JOIN experiments AS e
                ON e.id = br.experiment_id
            LEFT JOIN consensus_results AS cr
                ON cr.experiment_id = br.experiment_id
            WHERE br.benchmark_id = ?
            ORDER BY br.run_number
            """,
            (benchmark_id,),
        ).fetchall()

    return [dict(row) for row in rows]
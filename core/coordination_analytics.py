"""Data for the Coordination tab of the Analytics page.

Pure functions (no Streamlit): they read the runs recorded in the database
and return pandas objects.

What a Coordination run records
-------------------------------
The Coordination approach (Bach4Popper) has no held-out test set: the server
never scores the final hypothesis on unseen examples, and each client only
measures the candidates on its own training partition. This tab therefore
describes the SEARCH and its COST (solution found, rounds, programs tested,
time, size of the hypothesis), not predictive performance.

Comparison
----------
Coordination is compared with
  * Collaboration (same dataset, number of clients and partition): the other
    federated way to run Popper's generate-test-constrain loop;
  * the centralized Popper launched on the WHOLE dataset (no split). The
    centralized baselines of the Consensus tab are NOT used here: they train
    on 80 % of the examples, whereas Coordination and Collaboration train on
    all of them.

Repeated runs
-------------
For these approaches, the runs of a benchmark all use the same seed (hence
the same data and the same partition): they measure the run-to-run variation
of the search itself, so repeated runs are kept (unlike in the Consensus tab).
"""

from __future__ import annotations

import pandas as pd

from core.consensus_analytics import mean_and_se, rule_statistics
from database.connection import get_connection

APPROACH_LABELS = {
    "coordination": "Coordination",
    "collaboration": "Collaboration",
    "centralized": "Centralized (whole dataset)",
    "central_testing": "Client 0 (centralized)",
}


def _partition_name(value: str) -> str:
    return "IID" if value == "iid" else "Non-IID" if value == "non_iid" else str(value)


def load_search_runs() -> pd.DataFrame:
    """One row per completed run of Coordination, Collaboration (both inside a
    benchmark) or centralized Popper (launched without a split)."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                e.id AS experiment_id, e.approach, e.dataset,
                e.number_of_clients AS k, e.partition_strategy AS partition,
                e.learner, e.random_seed AS seed,
                br.benchmark_id, br.run_number, bm.name AS benchmark_name,
                s.solution, s.solution_found, s.all_clients_accepted,
                s.total_time_seconds, s.startup_time_seconds,
                s.learning_time_seconds, s.popper_time_seconds,
                s.federation_time_seconds,
                s.number_of_rounds, s.number_of_programs
            FROM experiments AS e
            JOIN server_results AS s ON s.experiment_id = e.id
            LEFT JOIN benchmark_runs AS br ON br.experiment_id = e.id
            LEFT JOIN benchmarks AS bm ON bm.id = br.benchmark_id
            WHERE e.status = 'COMPLETED'
              AND (
                    (e.approach IN ('coordination', 'collaboration')
                     AND br.benchmark_id IS NOT NULL)
                    -- Only the baselines launched on the whole dataset from a
                    -- benchmark ("Centralized, whole <dataset> · same seed as
                    -- #<id>"): single runs from the ILP page and older runs
                    -- made with other settings are not comparable.
                 OR (e.approach = 'centralized'
                     AND e.learner = 'popper'
                     AND e.reference_experiment_id IS NULL
                     AND br.benchmark_id IS NOT NULL
                     AND bm.name LIKE 'Centralized, whole%'
                     AND bm.status = 'COMPLETED')
              )
            """
        ).fetchall()

        client_rows = connection.execute(
            """
            SELECT experiment_id,
                   COUNT(*) AS n_clients,
                   SUM(number_of_examples) AS n_examples,
                   MAX(total_eval_wall_seconds) AS client_eval_max,
                   MAX(total_evaluate_phase_wall_seconds) AS eval_phase_max,
                   AVG(total_eval_wall_seconds) AS client_eval_mean,
                   SUM(COALESCE(accepted_solution, 0)) AS clients_accepting
            FROM client_results
            GROUP BY experiment_id
            """
        ).fetchall()

    frame = pd.DataFrame([dict(row) for row in rows])
    if frame.empty:
        return frame

    clients = pd.DataFrame([dict(row) for row in client_rows])
    if not clients.empty:
        frame = frame.merge(clients, on="experiment_id", how="left")
    else:
        for column in (
            "n_clients", "n_examples", "client_eval_max", "eval_phase_max",
            "client_eval_mean", "clients_accepting",
        ):
            frame[column] = float("nan")

    # A whole-dataset baseline is named "... same seed as #<benchmark id>":
    # that number is the federated benchmark it is the baseline of.
    frame["baseline_of"] = (
        frame["benchmark_name"]
        .astype("string")
        .str.extract(r"same seed as #(\d+)", expand=False)
        .astype("float")
    )

    # Hybrid evaluation, second search: a Coordination search tested by ONE
    # client holding the whole dataset. Saved as its own benchmark ("Centralized
    # testing, whole <dataset> · same seed as #<id>"); it has its own label so
    # it never mixes with the federated runs.
    is_central_testing = (
        frame["benchmark_name"].astype("string").str.startswith("Centralized testing").fillna(False)
    )
    frame.loc[is_central_testing, "approach"] = "central_testing"

    # Size of the learned hypothesis, from the stored solution text.
    statistics = frame["solution"].map(
        lambda text: rule_statistics(text.splitlines() if isinstance(text, str) else [])
    )
    frame["rules"] = [count if count else float("nan") for count, _ in statistics]
    frame["body_literals"] = [
        length if count else float("nan") for count, length in statistics
    ]

    frame["solution_found"] = frame["solution_found"].astype(float)
    # A centralized run has no clients to accept the solution.
    frame["accepted_by_all"] = frame["all_clients_accepted"].astype(float)
    frame.loc[frame["approach"] == "centralized", "accepted_by_all"] = float("nan")

    # A centralized run has no rounds: do not show 0 as if it were a count.
    centralized = frame["approach"] == "centralized"
    frame.loc[centralized, ["number_of_rounds", "number_of_programs"]] = float("nan")
    frame.loc[centralized, ["popper_time_seconds", "federation_time_seconds"]] = float("nan")

    # Split of the learning time (the parts overlap very little): the server
    # search itself, the time spent with the clients, and the rest.
    frame["time_search"] = frame["popper_time_seconds"]
    frame["time_federation"] = frame["federation_time_seconds"]
    frame["time_other"] = (
        frame["learning_time_seconds"] - frame["popper_time_seconds"] - frame["federation_time_seconds"]
    ).clip(lower=0.0)

    # Detailed split, the same one as the "Timing" card of the Experiments
    # page (core/benchmark_results.py):
    #   Total Popper time = Popper core (server) + client evaluation
    #   Federation overhead = time waiting for the clients - client evaluation
    # Client evaluation is the slowest client (max, not sum), since the
    # clients evaluate a program in parallel. "Not measured" is what is left
    # of the learning time once these two are taken out.
    client_eval = frame["client_eval_max"].fillna(0.0)
    evaluate_phase = frame["eval_phase_max"].fillna(0.0)
    frame["time_core"] = frame["popper_time_seconds"]
    frame["time_client_eval"] = client_eval.where(~centralized)
    frame["time_popper_total"] = frame["time_core"] + frame["time_client_eval"]
    frame["time_overhead"] = (
        frame["federation_time_seconds"] - client_eval - evaluate_phase
    ).clip(lower=0.0)
    frame["time_unmeasured"] = (
        frame["learning_time_seconds"] - frame["time_popper_total"] - frame["time_overhead"]
    )

    # Some older Collaboration runs were recorded with another timing
    # definition: a learning time of 0, or a time spent waiting for the
    # clients larger than the learning time. Their times are not reliable.
    federation = frame["federation_time_seconds"].fillna(0.0)
    frame["timing_ok"] = (frame["learning_time_seconds"] > 0) & (
        federation <= frame["learning_time_seconds"] * 1.05
    )

    for column in (
        "learning_time_seconds", "time_search", "time_federation", "time_other",
        "time_core", "time_client_eval", "time_popper_total", "time_overhead", "time_unmeasured",
    ):
        frame[f"{column}_checked"] = frame[column].where(frame["timing_ok"])

    frame["partition_name"] = frame["partition"].map(_partition_name)
    frame["series"] = frame["approach"].map(APPROACH_LABELS)
    return frame


def coordination_benchmarks(runs: pd.DataFrame, approach: str = "coordination") -> pd.DataFrame:
    """One row per benchmark of `approach` ("coordination" or "collaboration")
    that has at least one completed run."""
    coordination = runs[runs["approach"] == approach]
    if coordination.empty:
        return pd.DataFrame()
    return (
        coordination.groupby("benchmark_id")
        .agg(
            dataset=("dataset", "first"),
            learner=("learner", "first"),
            k=("k", "first"),
            partition=("partition", "first"),
            seed=("seed", "first"),
            n_runs=("experiment_id", "nunique"),
        )
        .reset_index()
        .sort_values(["dataset", "benchmark_id"])
    )


def comparison_frame(
    runs: pd.DataFrame,
    chosen_benchmarks: list[int],
    approach: str = "coordination",
    include_other: bool = True,
) -> pd.DataFrame:
    """The selected Coordination runs, next to the Collaboration runs with the
    same dataset, number of clients and partition (only if `include_other`),
    and the centralized Popper runs on the same dataset. The column `bar`
    names the setting."""

    other = "collaboration" if approach == "coordination" else "coordination"
    chosen = runs[(runs["approach"] == approach) & runs["benchmark_id"].isin(chosen_benchmarks)]
    if chosen.empty:
        return chosen

    pieces = []
    for (dataset, k, partition), group in chosen.groupby(["dataset", "k", "partition"]):
        bar = f"{dataset} · k={int(k)} · {_partition_name(partition)}"
        collaboration = runs[
            (runs["approach"] == other)
            & (runs["dataset"] == dataset)
            & (runs["k"] == k)
            & (runs["partition"] == partition)
        ]
        if not include_other:
            collaboration = collaboration.iloc[0:0]
        # Only the baseline(s) launched for the selected benchmark(s): same
        # dataset, same number of runs, same seed and settings.
        centralized = runs[
            (runs["approach"] == "centralized")
            & (runs["dataset"] == dataset)
            & runs["baseline_of"].isin(group["benchmark_id"].unique())
        ]
        for part in (group, collaboration, centralized):
            if not part.empty:
                pieces.append(part.assign(bar=bar))
    return pd.concat(pieces, ignore_index=True)


def time_breakdown_table(
    frame: pd.DataFrame, approach: str, labels: dict[int, str] | None = None
) -> pd.DataFrame:
    """One row per benchmark of `approach`: where the learning time goes.

    Mean ± standard deviation over the runs of the benchmark (as on the
    "Timing" card of the Experiments page). Runs with an unreliable timing
    are left out.

      Total Popper time  = Popper core (server) + client evaluation
      Learning time      = Total Popper time + Federation overhead + Not measured
    """

    def cell(values) -> str:
        # Small times keep their decimals (0.04 s must not show as 0.0).
        values = pd.Series(values).dropna()
        if values.empty:
            return "—"
        mean = values.mean()
        digits = 1 if abs(mean) >= 10 else 2 if abs(mean) >= 1 else 3
        return f"{mean:.{digits}f} ± {values.std(ddof=0):.{digits}f}"

    runs = frame[(frame["approach"] == approach) & frame["timing_ok"]]
    rows = []
    for benchmark_id, group in runs.groupby("benchmark_id", sort=True):
        label = (labels or {}).get(int(benchmark_id), f"#{int(benchmark_id)}")
        rows.append(
            {
                "Benchmark": label,
                "Runs": len(group),
                "Learning time (s)": cell(group["learning_time_seconds"]),
                "Total Popper time (s)": cell(group["time_popper_total"]),
                "= Popper core, server (s)": cell(group["time_core"]),
                "+ Client evaluation (s)": cell(group["time_client_eval"]),
                "Federation overhead (s)": cell(group["time_overhead"]),
                "Not measured (s)": cell(group["time_unmeasured"]),
            }
        )
    return pd.DataFrame(rows)


def side_by_side_table(frame: pd.DataFrame, approach: str) -> pd.DataFrame:
    """One row per benchmark of `approach`, the centralized run on the whole
    dataset in its own columns (same layout as the Consensus tab).

    Mean ± standard error over the runs. The centralized columns come from the
    baseline launched for that benchmark ("same seed as #<id>"); they show
    "—" when there is none. Rounds and programs tested exist only for the
    federated approach."""

    def cell(values, digits: int = 1) -> str:
        mean, se = mean_and_se(values)
        if mean != mean:
            return "—"
        return f"{mean:.{digits}f} ± {se:.{digits}f}"

    def rate(values) -> str:
        values = [v for v in values if v == v]
        return f"{100 * sum(values) / len(values):.0f} %" if values else "—"

    name = approach
    rows = []
    federated = frame[frame["approach"] == approach]
    for benchmark_id, group in federated.groupby("benchmark_id", sort=True):
        baseline = frame[
            (frame["approach"] == "centralized") & (frame["baseline_of"] == benchmark_id)
        ]
        first = group.iloc[0]
        rows.append(
            {
                "Benchmark": f"#{int(benchmark_id)}",
                "Dataset": first["dataset"],
                "Setting": f"k={int(first['k'])}, {_partition_name(first['partition']).lower()}, seed {int(first['seed'])}",
                "Runs": len(group),
                f"Solution found ({name})": rate(group["solution_found"]),
                "Solution found (centralized)": rate(baseline["solution_found"]),
                f"Rounds ({name})": cell(group["number_of_rounds"], 0),
                f"Programs tested ({name})": cell(group["number_of_programs"], 0),
                f"Rules ({name})": cell(group["rules"], 1),
                "Rules (centralized)": cell(baseline["rules"], 1),
                f"Literals ({name})": cell(group["body_literals"], 2),
                "Literals (centralized)": cell(baseline["body_literals"], 2),
                f"Time s ({name})": cell(group["learning_time_seconds_checked"], 1),
                "Time s (centralized)": cell(baseline["learning_time_seconds_checked"], 1),
            }
        )
    return pd.DataFrame(rows)


def hybrid_comparison_table(
    frame: pd.DataFrame, labels: dict[int, str] | None = None, approach: str = "coordination"
) -> pd.DataFrame:
    """Hybrid evaluation: for each Coordination benchmark, the federated search
    (clients 1..K, aggregated outcome) next to the same search tested by ONE
    client holding the whole dataset (client 0, centralized).

    Mean ± standard deviation over the runs. Popper core is the server's own
    work; client evaluation is the slowest client (for the federated search) or
    the single client (for the centralized testing)."""

    def cell(values, digits: int | None = None) -> str:
        values = pd.Series(values).dropna()
        if values.empty:
            return "—"
        mean = values.mean()
        d = digits if digits is not None else (1 if abs(mean) >= 10 else 2 if abs(mean) >= 1 else 3)
        return f"{mean:.{d}f} ± {values.std(ddof=0):.{d}f}"

    def rate(values) -> str:
        values = [v for v in values if v == v]
        return f"{100 * sum(values) / len(values):.0f} %" if values else "—"

    rows = []
    federated = frame[frame["approach"] == approach]
    for benchmark_id, group in federated.groupby("benchmark_id", sort=True):
        central = frame[
            (frame["approach"] == "central_testing") & (frame["baseline_of"] == benchmark_id)
        ]
        if central.empty:
            continue
        first = group.iloc[0]
        label = (labels or {}).get(int(benchmark_id), f"#{int(benchmark_id)}")
        for search, runs in (
            (f"Federated (k={int(first['k'])})", group),
            ("Client 0 (centralized)", central),
        ):
            rows.append(
                {
                    "Benchmark": label,
                    "Search": search,
                    "Runs": len(runs),
                    "Solution found": rate(runs["solution_found"]),
                    "Rounds": cell(runs["number_of_rounds"], 0),
                    "Programs tested": cell(runs["number_of_programs"], 0),
                    "Learning time (s)": cell(runs["learning_time_seconds_checked"]),
                    "Popper core, server (s)": cell(runs["time_core_checked"]),
                    "Client evaluation (s)": cell(runs["time_client_eval_checked"]),
                    "Federation overhead (s)": cell(runs["time_overhead_checked"]),
                }
            )
    return pd.DataFrame(rows)


def summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per setting and approach: mean ± standard error over runs."""

    def cell(values, digits: int = 1) -> str:
        mean, se = mean_and_se(values)
        if mean != mean:
            return "—"
        return f"{mean:.{digits}f} ± {se:.{digits}f}"

    def rate(values) -> str:
        values = [v for v in values if v == v]
        return f"{100 * sum(values) / len(values):.0f} %" if values else "—"

    rows = []
    for (bar, series), group in frame.groupby(["bar", "series"], sort=False):
        rows.append(
            {
                "Setting": bar,
                "Approach": series,
                "Runs": len(group),
                "Solution found": rate(group["solution_found"]),
                "Accepted by all clients": rate(group["accepted_by_all"]),
                "Rounds": cell(group["number_of_rounds"], 0),
                "Programs tested": cell(group["number_of_programs"], 0),
                "Learning time (s)": cell(group["learning_time_seconds_checked"], 1),
                "Server search (s)": cell(group["time_search_checked"], 2),
                "Waiting for clients (s)": cell(group["time_federation_checked"], 1),
                "Rules": cell(group["rules"], 1),
                "Body literals": cell(group["body_literals"], 2),
            }
        )
    return pd.DataFrame(rows)

"""Coordination tab of the Analytics page.

Same layout as the Consensus tab (benchmark selection, figures, table with
downloads), but for Learning by Coordination (Bach4Popper). This approach has
no held-out test set, so the tab studies the SEARCH and its COST: is a solution
found, how many rounds and programs, how the time is spent, how large the
hypothesis is. The approach is compared with the
centralized Popper on the whole dataset (see core/coordination_analytics.py).
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from apps.consensus_tab import _aggregate, _bars_with_error
from core import thesis_tables
from core.consensus_analytics import to_latex
from core.coordination_analytics import (
    APPROACH_LABELS,
    comparison_frame,
    coordination_benchmarks,
    load_search_runs,
    side_by_side_table,
    hybrid_comparison_table,
    time_breakdown_table,
)

COORDINATION = "#2F9E63"   # green, as in the rest of the Analytics page
COLLABORATION = "#F59E0B"  # orange
CENTRALIZED = "#E5484D"    # red
SERIES = {
    APPROACH_LABELS["coordination"]: COORDINATION,
    APPROACH_LABELS["collaboration"]: COLLABORATION,
    APPROACH_LABELS["centralized"]: CENTRALIZED,
}
PHASES = {
    "Server search (Popper)": "#3E7BFA",
    "Waiting for the clients": "#F59E0B",
    "Other": "#9CA3AF",
}


def _benchmark_label(row) -> str:
    partition = "IID" if row.partition == "iid" else "Non-IID" if row.partition == "non_iid" else row.partition
    return (
        f"#{int(row.benchmark_id)} · {row.dataset} · {str(row.learner).title()} · "
        f"k={int(row.k)} · {partition} · seed {int(row.seed)} · {int(row.n_runs)} run(s)"
    )


def _show_table(table: pd.DataFrame, key: str, caption: str, how_to_read: str, empty: str) -> None:
    """A table with its explanation and CSV / LaTeX downloads."""
    if table is None or table.empty:
        st.info(empty)
        return
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.caption(how_to_read)
    columns = st.columns(2)
    columns[0].download_button(
        "Download (CSV)", table.to_csv(index=False).encode("utf-8"),
        file_name=f"{key}.csv", mime="text/csv", key=f"{key}_csv",
    )
    columns[1].download_button(
        "Download (LaTeX)",
        to_latex(table, caption=caption, label=f"tab:{key.replace('_', '-')}").encode("utf-8"),
        file_name=f"{key}.tex", mime="text/plain", key=f"{key}_tex",
    )


def _render_thesis_tables(runs, chosen_benchmarks, approach: str, labels: dict, name: str) -> None:
    """One tab per sub-section of the results chapter; every table is built from
    the benchmarks selected above."""
    selected = runs[
        runs["benchmark_id"].isin(chosen_benchmarks) | runs["baseline_of"].isin(chosen_benchmarks)
    ]
    ids = list(chosen_benchmarks)
    hybrid = hybrid_comparison_table(selected, labels, approach)
    with st.container(border=True):
        st.markdown(
            f"**Tables of the results section — {name}.** One tab per sub-section. The federated search "
            "is compared, run by run, with the search of client 0 (centralized) and with Popper on the "
            "whole dataset; the tables use the benchmarks selected above."
        )
        tabs = st.tabs([
            "Equivalence", "Learned programs", "Non-IID", "Scalability", "Learning time", "Communication",
        ])

        with tabs[0]:
            _show_table(
                thesis_tables.equivalence_table(selected, ids, approach, labels),
                f"{approach}_equivalence",
                f"Equivalence of the federated search and of the search of client 0 ({name}).",
                "Two searches are equivalent when, at every round, they test the same program and obtain the "
                "same outcome and the same score. “First difference” is the round of the first difference, "
                "for each run that is not equivalent. “Same solution” compares the returned programs up to "
                "spaces and to the order of the body literals.",
                "Needs a federated benchmark and its client 0 (centralized) twin: tick “Hybrid evaluation” "
                "when launching a benchmark.",
            )

        with tabs[1]:
            _show_table(
                thesis_tables.programs_table(selected, ids, approach, labels),
                f"{approach}_programs",
                f"Learned programs ({name}).",
                "Number of rules and mean number of body literals per rule of the program returned by each search "
                "(mean ± standard deviation over the runs).",
                "No run with a solution in the selected benchmarks.",
            )

        with tabs[2]:
            non_iid_ids = [
                int(b) for b in selected[
                    (selected["approach"] == approach) & (selected["partition"] == "non_iid")
                ]["benchmark_id"].dropna().unique()
            ]
            _show_table(
                thesis_tables.equivalence_table(selected, non_iid_ids, approach, labels),
                f"{approach}_non_iid",
                f"Equivalence on non-IID partitions ({name}).",
                "Same table as “Equivalence”, restricted to the non-IID benchmarks selected above.",
                "Select a non-IID benchmark with its client 0 (centralized) twin.",
            )
            divergence = thesis_tables.divergence_table(selected, ids, approach, labels)
            if not divergence.empty:
                st.markdown("**Where the searches part.** First round at which a federated run differs from its client 0 run.")
                _show_table(
                    divergence, f"{approach}_divergence", f"First divergence ({name}).",
                    "“same program, different answer”: both searches test the same program but obtain another "
                    "outcome or score (the aggregation or the evaluation differs). “different programs”: the "
                    "earlier constraints already differed. “Clients” are the answers of the clients and "
                    "“Aggregated” their aggregation; “Client 0” is the answer on the whole dataset (score in brackets).",
                    "",
                )

        with tabs[3]:
            _show_table(
                thesis_tables.scalability_table(selected, ids, approach, labels),
                f"{approach}_scalability",
                f"Effect of the number of clients ({name}).",
                "One row per dataset, partition and number of clients K (mean ± standard deviation over the "
                "runs). Client evaluation is the slowest client.",
                "No run in the selected benchmarks.",
            )

        with tabs[4]:
            _show_table(
                hybrid,
                f"{approach}_learning_time",
                f"Learning time of the federated search and of client 0 ({name}).",
                "Learning time is the wall-clock time of the whole search. Popper core is the server's work "
                "(generating programs, building constraints); client evaluation is the slowest client "
                "(federated) or the only client (client 0); federation overhead is the waiting time of the "
                "server minus the client evaluation.",
                "No client 0 (centralized) run for the selected benchmarks.",
            )

        with tabs[5]:
            _show_table(
                thesis_tables.communication_table(selected, ids, approach, labels),
                f"{approach}_communication",
                f"Answers exchanged between the clients and the server ({name}).",
                "Counted from the hypothesis log: for each program, every client sends one answer (outcome "
                "and score) and, for each clause of the program, one clause-level answer (inconsistent, "
                "totally incomplete). No example, fact or rule is sent. Sizes in bytes are not measured.",
                "No run in the selected benchmarks.",
            )


def render_coordination_tab() -> None:
    render_search_tab("coordination")


def render_collaboration_tab() -> None:
    render_search_tab("collaboration")


def render_search_tab(approach: str) -> None:
    """Tab for Coordination or Collaboration: same study of the search and its
    cost; the whole-dataset centralized run
    is the comparison."""
    name = APPROACH_LABELS[approach]
    runs = load_search_runs()

    st.markdown(f"### Learning by {name}")

    benchmarks = coordination_benchmarks(runs, approach) if not runs.empty else pd.DataFrame()
    if benchmarks.empty:
        st.info(
            f"No completed {name} benchmark yet. Run one from the Simulation page "
            "(several runs give error bars)."
        )
        return

    labels = {int(row.benchmark_id): _benchmark_label(row) for row in benchmarks.itertuples()}

    # Default selection: for each dataset, the benchmark with the most runs.
    default_ids = (
        benchmarks.sort_values(["n_runs", "benchmark_id"])
        .groupby(["dataset", "k", "partition"])
        .tail(1)["benchmark_id"]
        .astype(int)
        .tolist()
    ) or list(labels)[:4]

    selection_key = f"{approach}_selected_benchmarks"
    if selection_key not in st.session_state:
        st.session_state[selection_key] = default_ids
    st.session_state[selection_key] = [key for key in st.session_state[selection_key] if key in labels]

    button_columns = st.columns([1.2, 1.2, 1.4, 6])
    button_columns[0].button(
        "Select all", key=f"{approach}_bench_all",
        on_click=lambda: st.session_state.__setitem__(selection_key, list(labels)),
    )
    button_columns[1].button(
        "Clear", key=f"{approach}_bench_none",
        on_click=lambda: st.session_state.__setitem__(selection_key, []),
    )
    button_columns[2].button(
        "Reset", key=f"{approach}_bench_reset",
        help="One benchmark per setting: the one with the most runs.",
        on_click=lambda: st.session_state.__setitem__(selection_key, default_ids),
    )
    chosen_benchmarks = st.pills(
        "Benchmarks (click to select or unselect)",
        list(labels),
        selection_mode="multi",
        format_func=lambda key: labels[key],
        key=selection_key,
    ) or []

    # Only this approach and the centralized run on the whole dataset.
    frame = comparison_frame(runs, chosen_benchmarks, approach, include_other=False)
    if frame.empty:
        st.info("Select at least one benchmark.")
        return

    series_colors = {
        APPROACH_LABELS[approach]: SERIES[APPROACH_LABELS[approach]],
        APPROACH_LABELS["centralized"]: SERIES[APPROACH_LABELS["centralized"]],
    }
    coordination_runs = frame[frame["approach"] == approach]
    has_centralized = bool((frame["approach"] == "centralized").any())

    st.caption(
        f"{len(coordination_runs)} {name} run(s) in the selected benchmarks. Bars show the mean "
        "over runs and the standard error. The runs of a benchmark use the same seed, hence the same "
        "data and partition: the error bars measure the variation of the search from one run to "
        "another, not the variation between data splits."
    )
    st.caption(
        f"{name} has no held-out test set (the final hypothesis is not scored on unseen "
        "examples), so this tab shows the search and its cost, not predictive performance."
    )
    ignored_timing = int((~frame["timing_ok"]).sum())
    if ignored_timing:
        st.caption(
            f"{ignored_timing} run(s) were ignored in the time figures and columns: they were recorded "
            "with an older timing definition (learning time of 0, or time spent waiting for the clients "
            "larger than the learning time)."
        )
    missing = []
    if not has_centralized:
        missing.append(
            "no centralized Popper run on the whole dataset launched for the selected benchmark "
            "(use the “Run centralized on the whole dataset” button on the Experiments page; the "
            "baselines of the Consensus tab train on 80 % of the examples, so they are not used here)"
        )
    if missing:
        st.caption("Missing for the comparison: " + "; ".join(missing) + ".")

    def comparison(column: str) -> pd.DataFrame:
        pieces = []
        for series, part in frame.groupby("series", sort=False):
            aggregated = _aggregate(part.dropna(subset=[column]), ["bar"], column)
            if aggregated.empty:
                continue
            aggregated["series"] = series
            pieces.append(aggregated)
        return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()

    # ------------------------------------------------------------------
    # Figure 1 — outcome of the search
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            "**Figure 1 — Outcome of the search.** Share of the runs in which the search returned a "
            "solution, and in which every client accepted it (complete and consistent on its own "
            "partition)."
        )
        outcome_columns = st.columns(2)
        for box, (title, column) in zip(
            outcome_columns,
            (("Solution found", "solution_found"), ("Accepted by all clients", "accepted_by_all")),
        ):
            data = comparison(column)
            with box:
                if data.empty:
                    st.info("No data.")
                else:
                    st.altair_chart(
                        _bars_with_error(
                            data, "bar", "series", title, series_colors, "share of runs", height=300,
                        ),
                        use_container_width=True,
                    )

    # ------------------------------------------------------------------
    # Figure 2 — cost: time and size of the hypothesis
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            "**Figure 2 — Cost and size of the hypothesis.** Learning time of the server (log scale), "
            "rules and body literals of the returned hypothesis."
        )
        cost_columns = st.columns(3)
        for box, (title, column, y_title, log_scale) in zip(
            cost_columns,
            (
                ("Learning time (log scale)", "learning_time_seconds_checked", "seconds (log)", True),
                ("Rules", "rules", "rules", False),
                ("Body literals per rule", "body_literals", "literals", False),
            ),
        ):
            data = comparison(column)
            with box:
                if data.empty:
                    st.info("No data.")
                else:
                    st.altair_chart(
                        _bars_with_error(
                            data, "bar", "series", title, series_colors, y_title,
                            height=300, unit_scale=False, log_scale=log_scale,
                        ),
                        use_container_width=True,
                    )

    # ------------------------------------------------------------------
    # Figure 3 — search effort (federated approaches only)
    # ------------------------------------------------------------------
    federated = frame[frame["approach"] != "centralized"]
    with st.container(border=True):
        st.markdown(
            "**Figure 3 — Search effort.** Number of rounds and of candidate programs tested by the "
            "clients before the search ends."
        )
        effort_columns = st.columns(2)
        for box, (title, column, y_title) in zip(
            effort_columns,
            (("Rounds", "number_of_rounds", "rounds"), ("Programs tested", "number_of_programs", "programs")),
        ):
            pieces = []
            for series, part in federated.groupby("series", sort=False):
                aggregated = _aggregate(part.dropna(subset=[column]), ["bar"], column)
                if not aggregated.empty:
                    pieces.append(aggregated.assign(series=series))
            data = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()
            with box:
                if data.empty:
                    st.info("No data.")
                else:
                    st.altair_chart(
                        _bars_with_error(
                            data, "bar", "series", title, series_colors, y_title,
                            height=300, unit_scale=False,
                        ),
                        use_container_width=True,
                    )

    # ------------------------------------------------------------------
    # Figure 4 — where the time goes
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            "**Figure 4 — Where the time goes.** Mean learning time split between the search run by "
            "the server, the time spent waiting for the clients (it includes their evaluation of the "
            "candidates), and the rest."
        )
        breakdown = (
            federated.groupby(["bar", "series"], sort=False)[
                ["time_search_checked", "time_federation_checked", "time_other_checked"]
            ]
            .mean()
            .reset_index()
            .melt(id_vars=["bar", "series"], var_name="phase", value_name="seconds")
        )
        breakdown["phase"] = breakdown["phase"].map(
            {
                "time_search_checked": "Server search (Popper)",
                "time_federation_checked": "Waiting for the clients",
                "time_other_checked": "Other",
            }
        )
        breakdown = breakdown.dropna(subset=["seconds"])
        breakdown["label"] = breakdown["bar"] + " · " + breakdown["series"]
        if breakdown.empty:
            st.info("No data.")
        else:
            chart = (
                alt.Chart(breakdown)
                .mark_bar()
                .encode(
                    y=alt.Y("label:N", title=None, sort=None),
                    x=alt.X("seconds:Q", title="seconds", stack="zero"),
                    color=alt.Color(
                        "phase:N",
                        title=None,
                        scale=alt.Scale(domain=list(PHASES), range=list(PHASES.values())),
                        legend=alt.Legend(orient="bottom", symbolType="circle"),
                    ),
                    tooltip=["label", "phase", alt.Tooltip("seconds:Q", format=".2f")],
                )
                .properties(height=max(120, 46 * breakdown["label"].nunique()))
            )
            st.altair_chart(chart, use_container_width=True)

    # ------------------------------------------------------------------
    # Figure 5 — run-to-run variation
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            "**Figure 5 — Each run.** Learning time of every run (log scale). The runs of a benchmark "
            "use the same data, so the spread comes from the search itself."
        )
        points = frame.dropna(subset=["learning_time_seconds_checked"]).copy()
        points = points[points["learning_time_seconds_checked"] > 0]
        if points.empty:
            st.info("No data.")
        else:
            chart = (
                alt.Chart(points)
                .mark_circle(size=90, opacity=0.85)
                .encode(
                    x=alt.X("bar:N", title=None, sort=None, axis=alt.Axis(labelAngle=-30, labelLimit=220)),
                    xOffset=alt.XOffset("series:N"),
                    y=alt.Y("learning_time_seconds_checked:Q", title="seconds (log)", scale=alt.Scale(type="log")),
                    color=alt.Color(
                        "series:N",
                        title=None,
                        scale=alt.Scale(domain=list(series_colors), range=list(series_colors.values())),
                        legend=alt.Legend(orient="bottom", symbolType="circle"),
                    ),
                    tooltip=[
                        "series",
                        "bar",
                        alt.Tooltip("experiment_id:Q", title="Experiment"),
                        alt.Tooltip("learning_time_seconds_checked:Q", title="Time (s)", format=".2f"),
                        alt.Tooltip("number_of_rounds:Q", title="Rounds"),
                        alt.Tooltip("rules:Q", title="Rules"),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)

    # ------------------------------------------------------------------
    # Table — where the learning time goes, per benchmark
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            "**Table — Where the learning time goes, per benchmark.** Mean ± standard deviation "
            "over the runs of each benchmark."
        )
        time_table = time_breakdown_table(frame, approach, labels)
        if time_table.empty:
            st.info("No run with a reliable timing in the selected benchmarks.")
        else:
            st.dataframe(time_table, use_container_width=True, hide_index=True)
            st.caption(
                "**How to read it.** “Learning time” is measured directly, as the wall-clock time of "
                "the whole search (from the moment the clients are ready to the end of the search): "
                "it is not a sum. “Total Popper time” = “Popper core (server)” + “Client evaluation”. "
                "Popper core is the server's own work: generating a program, and turning the "
                "outcome into constraints. Client evaluation is the slowest client's time testing the "
                "programs on its examples (the clients work in parallel). “Federation overhead” is the "
                "time spent waiting for the clients, without their evaluation time. "
                "“Not measured” = Learning time − Total Popper time − Federation overhead: time spent in "
                "none of these three parts. It should be small."
            )
            st.download_button(
                "Download this table (CSV)",
                time_table.to_csv(index=False).encode("utf-8"),
                file_name=f"{approach}_time_breakdown.csv",
                mime="text/csv",
                key=f"{approach}_time_breakdown_csv",
            )

    # ------------------------------------------------------------------
    # Table — hybrid evaluation (federated learning + centralized testing)
    # ------------------------------------------------------------------
    hybrid = hybrid_comparison_table(
        runs[
            runs["benchmark_id"].isin(chosen_benchmarks)
            | runs["baseline_of"].isin(chosen_benchmarks)
        ],
        labels,
        approach,
    )
    with st.container(border=True):
        st.markdown(
            "**Table — Hybrid evaluation: federated search against client 0 (centralized).** "
            "Mean ± standard deviation over the runs."
        )
        if hybrid.empty:
            st.info(
                "No client 0 (centralized) run for the selected benchmarks. Keep “Hybrid "
                "evaluation” ticked when launching a benchmark."
            )
        else:
            st.dataframe(hybrid, use_container_width=True, hide_index=True)
            st.caption(
                "Two complete generate-test-constrain searches of the same dataset. In the "
                "federated one, the clients test each program on their part of the examples and "
                "the server aggregates their outcomes (ALL/SOME/NONE) to build the constraints. "
                "In the client 0 (centralized) one, a single client holding the whole dataset tests "
                "each program and its outcome gives the constraints directly. Popper core is the "
                "server's own work (generating programs, building constraints); client evaluation "
                "is the slowest client (federated) or the only client (client 0)."
            )
            st.download_button(
                "Download this table (CSV)",
                hybrid.to_csv(index=False).encode("utf-8"),
                file_name=f"{approach}_hybrid_evaluation.csv",
                mime="text/csv",
                key=f"{approach}_hybrid_csv",
            )

    # ------------------------------------------------------------------
    # Tables of the thesis, one per sub-section of the results
    # ------------------------------------------------------------------
    _render_thesis_tables(runs, chosen_benchmarks, approach, labels, name)

    # ------------------------------------------------------------------
    # Table — summary and downloads
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            f"**Cost and size of the theory** — {name} against the centralized run on the whole "
            "dataset, mean ± standard error over runs."
        )
        table = side_by_side_table(frame, approach)
        st.dataframe(table, use_container_width=True, hide_index=True)
        st.caption(
            "**How to read it.** “Runs” = number of runs of the benchmark. “Solution found” = share of "
            "runs whose search returned a solution. “Rounds” = exchanges between the server and the "
            "clients; “Programs tested” = candidates sent to the clients. Rules and literals are per hypothesis (literals = body literals per rule). "
            "The centralized columns come from the run on the whole dataset launched for that benchmark; "
            "“—” = no such run, or not defined (a centralized run has no clients and no rounds)."
        )
        download_columns = st.columns(3)
        download_columns[0].download_button(
            "Download the table (CSV)",
            table.to_csv(index=False).encode("utf-8"),
            file_name=f"{approach}_summary.csv",
            mime="text/csv",
        )
        download_columns[1].download_button(
            "Download the table (LaTeX)",
            to_latex(
                table,
                caption=f"Search and cost of Learning by {name} (mean $\\pm$ standard error over runs).",
                label=f"tab:{approach}-results",
            ).encode("utf-8"),
            file_name=f"{approach}_summary.tex",
            mime="text/plain",
        )
        download_columns[2].download_button(
            "Download all runs (CSV)",
            frame.drop(columns=["solution"]).to_csv(index=False).encode("utf-8"),
            file_name=f"{approach}_runs.csv",
            mime="text/csv",
        )

    # ------------------------------------------------------------------
    # Hypotheses found
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(f"**Hypotheses returned by the {name} runs.**")
        listing = coordination_runs[
            ["experiment_id", "bar", "run_number", "number_of_rounds", "learning_time_seconds", "solution"]
        ].rename(
            columns={
                "experiment_id": "Experiment",
                "bar": "Setting",
                "run_number": "Run",
                "number_of_rounds": "Rounds",
                "learning_time_seconds": "Time (s)",
                "solution": "Hypothesis",
            }
        )
        st.dataframe(listing, use_container_width=True, hide_index=True)

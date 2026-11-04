"""Consensus tab of the Analytics page: figures that answer the questions an
experimental section on Learning by Consensus asks.

  Q1  Does the consensus match the centralized learner?        (figure 1, table)
  Q2  Does the vote beat its members?                          (figure 2, 7)
  Q3  Is the consensus simpler than the centralized theory?    (figure 3)
  Q4  How many clients?                                        (figure 4)
  Q5  IID or label imbalance?                                  (figure 5)
  Q6  What does it cost?                                       (figure 6)

The centralized baseline is launched from the Experiments page ("Run
centralized on the same data"): the learner runs once on the whole training
set and is scored on the same test set as the consensus run it is linked to.
"""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from core.consensus_analytics import (
    BASELINE_LABEL,
    agreement_matrix,
    cost_table,
    keep_one_run_per_seed,
    load_consensus_runs,
    load_partitions,
    load_vote_traces,
    mean_and_se,
    summary_table,
    to_latex,
)

# Vivid palette for the figures (the rest of the app is navy / grey).
NAVY = "#3E7BFA"      # blue
GREY = "#F59E0B"      # orange
LIGHT = "#2F9E63"     # green
RED = "#E5484D"
PURPLE = "#7C5CFC"
PINK = "#E9578C"
TEAL = "#14B8A6"
PALETTE = [NAVY, GREY, LIGHT, RED, PURPLE, PINK, TEAL]
CENTRALIZED_LABEL = "Centralized (same split)"
SERIES = {
    "Consensus": NAVY,
    "Average client (alone)": GREY,
    "Best client (alone)": LIGHT,
    CENTRALIZED_LABEL: RED,
    "Majority class": "#9CA3AF",
}
METRICS = {
    "accuracy": "Accuracy",
    "mcc": "MCC",
    "f1": "F1",
    "precision": "Precision",
    "recall": "Recall",
}


def _aggregate(frame: pd.DataFrame, keys: list[str], value: str) -> pd.DataFrame:
    rows = []
    for key, group in frame.groupby(keys):
        mean, se = mean_and_se(group[value])
        key = key if isinstance(key, tuple) else (key,)
        rows.append({**dict(zip(keys, key)), "mean": mean, "se": se, "runs": len(group)})
    result = pd.DataFrame(rows)
    if not result.empty:
        result["lo"] = result["mean"] - result["se"]
        result["hi"] = result["mean"] + result["se"]
    return result


def _bars_with_error(
    data: pd.DataFrame,
    x: str,
    color: str | None,
    title: str,
    domain: dict | None = None,
    y_title: str = "",
    height: int = 320,
    single_color: str = NAVY,
    unit_scale: bool = True,
    log_scale: bool = False,
) -> alt.LayerChart:
    encode_x = alt.X(f"{x}:N", title=None, sort=None, axis=alt.Axis(labelAngle=-30, labelLimit=200, labelOverlap=False))
    offset = alt.XOffset(f"{color}:N") if color else alt.XOffset()
    color_encoding = (
        alt.Color(
            f"{color}:N",
            title=None,
            scale=alt.Scale(domain=list(domain.keys()), range=list(domain.values()))
            if domain
            else alt.Undefined,
            legend=alt.Legend(orient="bottom", symbolType="circle"),
        )
        if color
        else alt.value(single_color)
    )
    tooltip = [x] + ([color] if color else []) + [
        alt.Tooltip("mean:Q", format=".3f"),
        alt.Tooltip("se:Q", title="± SE", format=".3f"),
        alt.Tooltip("runs:Q", title="Runs"),
    ]
    bars = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=encode_x,
            xOffset=offset,
            y=alt.Y(
                "mean:Q",
                title=y_title,
                scale=(
                    alt.Scale(type="log", domain=[0.1, float(data["hi"].max()) * 1.5], clamp=True)
                    if log_scale
                    else alt.Scale(domain=[0, 1]) if unit_scale else alt.Undefined
                ),
            ),
            color=color_encoding,
            tooltip=tooltip,
        )
    )
    if log_scale:
        data = data.assign(lo=data["lo"].clip(lower=0.1))
    errors = (
        alt.Chart(data)
        .mark_rule(color="#0F1B33")
        .encode(x=encode_x, xOffset=offset, y="lo:Q", y2="hi:Q")
    )
    return alt.layer(bars, errors).properties(height=height, title=title)


def render_consensus_tab() -> None:
    runs, repeated_runs = keep_one_run_per_seed(load_consensus_runs())

    st.markdown("### Learning by Consensus")

    if runs.empty:
        st.info(
            "No completed Consensus benchmark yet. Run one from the "
            "Simulation page (several seeds give error bars)."
        )
        return

    # ------------------------------------------------------------------
    # Benchmark selection (the only filter)
    # ------------------------------------------------------------------
    # One toggle per benchmark: select the benchmarks to compare, everything
    # below (figures, table, partitions) is computed from them alone.
    benchmarks = (
        runs.groupby("benchmark_id")
        .agg(
            dataset=("dataset", "first"),
            learner=("learner", "first"),
            k=("k", "first"),
            partition=("partition", "first"),
            n_runs=("seed", "nunique"),
            has_baseline=("baseline_accuracy", lambda v: bool(v.notna().any())),
        )
        .reset_index()
        .sort_values(["dataset", "benchmark_id"])
    )

    def benchmark_label(row) -> str:
        partition_name = "IID" if row.partition == "iid" else "Non-IID" if row.partition == "non_iid" else row.partition
        return (
            f"#{int(row.benchmark_id)} · {row.dataset} · {row.learner.title()} · "
            f"k={int(row.k)} · {partition_name} · {int(row.n_runs)} run(s)"
            + ("" if row.has_baseline else " · no centralized")
        )

    labels = {int(row.benchmark_id): benchmark_label(row) for row in benchmarks.itertuples()}

    # Default selection: for each dataset, the Popper benchmark with 3 clients and an
    # IID partition that has a centralized baseline and the most runs.
    default_ids = (
        benchmarks[
            (benchmarks["learner"] == "popper") & (benchmarks["k"] == 3) & (benchmarks["partition"] == "iid")
        ]
        .sort_values(["has_baseline", "n_runs", "benchmark_id"])
        .groupby(["dataset", "k", "partition"])
        .tail(1)["benchmark_id"]
        .astype(int)
        .tolist()
    ) or list(labels)[:4]

    selection_key = "consensus_selected_benchmarks"
    if selection_key not in st.session_state:
        st.session_state[selection_key] = default_ids
    st.session_state[selection_key] = [
        key for key in st.session_state[selection_key] if key in labels
    ]

    button_columns = st.columns([1.2, 1.2, 1.4, 6])
    button_columns[0].button(
        "Select all", key="consensus_bench_all",
        on_click=lambda: st.session_state.__setitem__(selection_key, list(labels)),
    )
    button_columns[1].button(
        "Clear", key="consensus_bench_none",
        on_click=lambda: st.session_state.__setitem__(selection_key, []),
    )
    button_columns[2].button(
        "Reset", key="consensus_bench_reset",
        help="One benchmark per dataset: the most complete Popper run.",
        on_click=lambda: st.session_state.__setitem__(selection_key, default_ids),
    )
    chosen_benchmarks = st.pills(
        "Benchmarks (click to select or unselect)",
        list(labels),
        selection_mode="multi",
        format_func=lambda key: labels[key],
        key=selection_key,
    ) or []

    metric = st.selectbox(
        "Metric of the table", list(METRICS), format_func=lambda m: METRICS[m],
        help="The figures below always show accuracy and MCC.",
    )

    frame = runs[runs["benchmark_id"].isin(chosen_benchmarks)]
    if frame.empty:
        st.info("Select at least one benchmark.")
        return

    frame = frame.copy()
    frame["group"] = frame["dataset"] + " · " + frame["learner"]
    # Bar label: the dataset, plus the setting only when it is not obvious.
    multiple_settings = frame.groupby("dataset")["benchmark_id"].nunique().max() > 1
    multiple_learners = frame["learner"].nunique() > 1
    frame["bar"] = frame["dataset"] + frame.apply(
        lambda r: (f" · {r['learner'].title()}" if multiple_learners else "")
        + (f" · {r['setting']}" if multiple_settings else ""),
        axis=1,
    )

    if repeated_runs:
        st.caption(
            f"{repeated_runs} run(s) repeated with the same settings and the same seed were "
            "ignored: they use the same split, so they are not independent runs."
        )
    baseline_rows = int(frame["baseline_accuracy"].notna().sum())
    st.caption(
        f"{len(frame)} runs in the selected benchmarks. Bars show the mean over runs (seeds) and "
        "the standard error. "
        + (
            f"“{CENTRALIZED_LABEL}” is the learner run once on the whole training set and "
            f"scored on the same test set ({baseline_rows} run(s) linked)."
            if baseline_rows
            else "No centralized baseline yet: open a Consensus experiment in the "
            "Experiments page and press “Run centralized on the same data”."
        )
    )
    if (frame.groupby("bar").size() < 3).all():
        st.warning(
            "Most selected benchmarks have fewer than 3 runs: error bars and p-values need "
            "several seeds."
        )

    # ------------------------------------------------------------------
    # Figure 1 — predictive performance (accuracy and MCC)
    # ------------------------------------------------------------------
    def comparison(columns: list[tuple[str, str]], unit_scale: bool = True):
        pieces = []
        for label, column in columns:
            aggregated = _aggregate(frame.dropna(subset=[column]), ["bar"], column)
            if aggregated.empty:
                continue
            aggregated["series"] = label
            pieces.append(aggregated)
        return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()

    with st.container(border=True):
        st.markdown(
            "**Figure 1 — Predictive performance.** The consensus (majority vote of all clients) next "
            "to what each client achieves alone with its own local hypothesis H_i (average and best "
            "client), and to the centralized baseline, all on the same test set."
        )
        chart_columns = st.columns(2)
        for column_box, (key, name) in zip(chart_columns, (("accuracy", "Accuracy"), ("mcc", "MCC"))):
            data = comparison([
                ("Consensus", f"consensus_{key}"),
                ("Average client (alone)", f"mean_h_{key}"),
                ("Best client (alone)", f"best_h_{key}"),
                (CENTRALIZED_LABEL, f"baseline_{key}"),
            ] + ([("Majority class", "majority_class")] if key == "accuracy" else []))
            with column_box:
                if data.empty:
                    st.info(f"No {name} available.")
                else:
                    colors = SERIES if key == "accuracy" else {
                        label: color for label, color in SERIES.items() if label != "Majority class"
                    }
                    chart = _bars_with_error(
                        data, "bar", "series", name, colors, name, unit_scale=(key == "accuracy"),
                    )
                    st.altair_chart(chart, use_container_width=True)

    # ------------------------------------------------------------------
    # Figure 2 — what it costs and how complex the theory is
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            "**Figure 2 — Cost and size of the theory.** Learning time of the consensus is that "
            "of the slowest client (clients learn in parallel); rules and literals are per "
            "hypothesis."
        )
        cost_series = {"Consensus": NAVY, CENTRALIZED_LABEL: RED}
        cost_columns = st.columns(3)
        for column_box, (title, consensus_column, baseline_column, y_title) in zip(
            cost_columns,
            (
                ("Learning time (log scale)", "time_slowest", "baseline_time", "seconds (log)"),
                ("Rules per hypothesis", "rules_per_hypothesis", "baseline_rules", "rules"),
                ("Body literals per rule", "body_literals", "baseline_body", "literals"),
            ),
        ):
            data = comparison([
                ("Consensus", consensus_column),
                (CENTRALIZED_LABEL, baseline_column),
            ])
            with column_box:
                if data.empty:
                    st.info("No data.")
                else:
                    st.altair_chart(
                        _bars_with_error(
                            data, "bar", "series", title, cost_series, y_title,
                            height=300, unit_scale=False,
                            log_scale=title.startswith("Learning time"),
                        ),
                        use_container_width=True,
                    )

    # ------------------------------------------------------------------
    # Table — summary and significance
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            f"**Table — {METRICS[metric]}, mean ± standard error over runs, with a "
            "paired t-test of the consensus against the centralized baseline "
            "(same seeds).**"
        )
        table = summary_table(frame, metric)
        shown_table = table.copy()
        shown_table["p (consensus vs centralized)"] = shown_table[
            "p (consensus vs centralized)"
        ].map(lambda value: f"{value:.3f}" if value == value else "needs ≥ 3 runs")
        st.dataframe(shown_table, use_container_width=True, hide_index=True)
        st.caption(
            "**How to read it.** “Runs” = number of seeds. “±” = standard error of the mean over "
            "these runs (the spread between seeds divided by √runs): the smaller it is, the more "
            "stable the mean. “Average / Best client (alone)” = the local hypotheses H_i taken "
            "one by one. p = paired t-test of the consensus against the centralized learner "
            "(same seeds); it needs at least 3 runs, and “--” in LaTeX means no difference "
            "to test."
        )
        cost = cost_table(frame)
        st.markdown(
            "**Cost and size of the theory** — rules and body literals per hypothesis, learning "
            "time (consensus: slowest client, since clients learn in parallel) and data sent by "
            "the clients."
        )
        st.dataframe(cost, use_container_width=True, hide_index=True)
        st.download_button(
            "Download the cost table (CSV)",
            cost.to_csv(index=False).encode("utf-8"),
            file_name="consensus_cost.csv",
            mime="text/csv",
        )
        download_columns = st.columns(3)
        download_columns[0].download_button(
            "Download the table (CSV)",
            table.to_csv(index=False).encode("utf-8"),
            file_name="consensus_summary.csv",
            mime="text/csv",
        )
        download_columns[1].download_button(
            "Download the table (LaTeX)",
            to_latex(
                table,
                caption=f"{METRICS[metric]} of Learning by Consensus (mean $\\pm$ standard error over runs).",
                label="tab:consensus-results",
            ).encode("utf-8"),
            file_name="consensus_summary.tex",
            mime="text/plain",
        )
        download_columns[2].download_button(
            "Download all runs (CSV)",
            frame.drop(columns=["group", "bar"]).to_csv(index=False).encode("utf-8"),
            file_name="consensus_runs.csv",
            mime="text/csv",
        )


    # ------------------------------------------------------------------
    # Data — how the examples are partitioned (tables, like a paper)
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            "**Data — Partition of the examples.** Choose the experiments: for each one, a table "
            "gives the positive and negative examples of the dataset, of the train and test sets, "
            "and of each client."
        )
        mode = st.radio(
            "Choose by",
            ["Datasets (automatic)", "Experiments (manual)"],
            horizontal=True,
            key="consensus_partition_mode",
            help="Datasets: one table for each dataset selected in the filter at the top of "
            "the page. Experiments: you pick the exact experiments.",
        )
        seeds = sorted(frame["seed"].unique())
        chosen_runs = pd.DataFrame()

        if mode.startswith("Datasets"):
            federated_frame = frame[frame["k"] > 1]
            if federated_frame.empty:
                st.info("No federated run in the current selection.")
            else:
                option_columns = st.columns(3)
                k_options = sorted(federated_frame["k"].unique())
                k_choice = option_columns[0].selectbox(
                    "Number of clients", k_options,
                    index=k_options.index(3) if 3 in k_options else 0,
                    key="consensus_partition_k",
                )
                partition_options = sorted(
                    federated_frame[federated_frame["k"] == k_choice]["partition"].unique()
                )
                strategy_choice = option_columns[1].selectbox(
                    "Partition", partition_options,
                    index=partition_options.index("iid") if "iid" in partition_options else 0,
                    format_func=lambda key: "IID" if key == "iid" else "Non-IID" if key == "non_iid" else key,
                    key="consensus_partition_strategy",
                )
                matching = federated_frame[
                    (federated_frame["k"] == k_choice)
                    & (federated_frame["partition"] == strategy_choice)
                ]
                matching_seeds = sorted(matching["seed"].unique())
                seed_pick = option_columns[2].selectbox(
                    "Seed", matching_seeds, key="consensus_partition_seed_auto",
                    help="The partition depends on the seed, not on the learner.",
                )
                # One run per dataset: the partition does not depend on the learner.
                chosen_runs = (
                    matching[matching["seed"] == seed_pick]
                    .sort_values(["dataset", "benchmark_id"])
                    .drop_duplicates("dataset")
                    .reset_index(drop=True)
                )
                missing = [
                    d for d in sorted(frame["dataset"].unique())
                    if d not in set(chosen_runs["dataset"])
                ]
                if missing:
                    st.caption(
                        "No run with these settings yet for: " + ", ".join(missing) + "."
                    )
        else:
            experiments = (
                frame.sort_values(["dataset", "k", "partition", "benchmark_id"])
                .drop_duplicates("benchmark_id")[["benchmark_id", "dataset", "k", "partition", "learner"]]
            )
            partition_labels = {
                int(row.benchmark_id): f"#{int(row.benchmark_id)} · {row.dataset} · k={int(row.k)} · {row.partition} · {row.learner}"
                for row in experiments.itertuples()
            }
            selection_key = "consensus_partition_experiments"
            if selection_key not in st.session_state:
                st.session_state[selection_key] = list(partition_labels)[:4]
            # Forget selected experiments that the filters above have removed.
            st.session_state[selection_key] = [
                key for key in st.session_state[selection_key] if key in partition_labels
            ]

            button_columns = st.columns([1, 1, 6])
            button_columns[0].button(
                "Select all", key="consensus_partition_all",
                on_click=lambda: st.session_state.__setitem__(selection_key, list(partition_labels)),
            )
            button_columns[1].button(
                "Clear", key="consensus_partition_none",
                on_click=lambda: st.session_state.__setitem__(selection_key, []),
            )
            chosen_ids = st.pills(
                "Experiments (click to select or unselect)",
                list(partition_labels),
                selection_mode="multi",
                format_func=lambda key: partition_labels[key],
                key=selection_key,
            ) or []
            seed_choice = (
                st.selectbox(
                    "Seed", seeds, key="consensus_partition_seed",
                    help="The partition depends on the seed. If an experiment has no run with "
                    "this seed, its first run is shown.",
                )
                if len(seeds) > 1
                else seeds[0]
            )
            shown = []
            for benchmark_id in chosen_ids:
                runs_of = frame[frame["benchmark_id"] == benchmark_id].sort_values("seed")
                preferred = runs_of[runs_of["seed"] == seed_choice]
                shown.append((preferred if not preferred.empty else runs_of).iloc[[0]])
            if shown:
                chosen_runs = pd.concat(shown, ignore_index=True)

        if chosen_runs.empty:
            st.info("Nothing to show: select at least one dataset or experiment.")
        else:
            raw = load_partitions(chosen_runs)

            tables = []
            for _, run in chosen_runs.iterrows():
                mine = raw[raw["experiment_id"] == run["experiment_id"]]
                clients = mine[mine["part"] != "Test (common)"].sort_values("order")
                test = mine[mine["part"] == "Test (common)"].iloc[0]
                train_pos, train_neg = int(clients["pos"].sum()), int(clients["neg"].sum())
                rows = [
                    (run["dataset"], train_pos + int(test["pos"]), train_neg + int(test["neg"])),
                    ("Train", train_pos, train_neg),
                    ("Test", int(test["pos"]), int(test["neg"])),
                ] + [(r.part, int(r.pos), int(r.neg)) for r in clients.itertuples()]
                table = pd.DataFrame(rows, columns=["Partition", "Positives", "Negatives"])
                table["Total"] = table["Positives"] + table["Negatives"]
                partition_name = "IID" if run["partition"] == "iid" else "Non-IID"
                tables.append(
                    (f"{run['dataset']} · {int(run['k'])} clients · {partition_name} · seed {int(run['seed'])} · from experiment #{int(run['benchmark_id'])}", table)
                )

            columns = st.columns(2)
            for position, (title, table) in enumerate(tables):
                with columns[position % 2]:
                    st.markdown(f"**({chr(ord('a') + position % 26)}) {title}**")
                    st.dataframe(
                        table, hide_index=True, use_container_width=True,
                        height=min(38 + 35 * len(table), 460),
                    )

            export = pd.concat(
                [table.assign(Experiment=title) for title, table in tables], ignore_index=True
            )[["Experiment", "Partition", "Positives", "Negatives", "Total"]]
            st.download_button(
                "Download these tables (CSV)",
                export.to_csv(index=False).encode("utf-8"),
                file_name="consensus_partitions.csv",
                mime="text/csv",
            )


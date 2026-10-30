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
    load_consensus_runs,
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
    "Mean of the H_i": GREY,
    "Best H_i": LIGHT,
    CENTRALIZED_LABEL: RED,
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
) -> alt.LayerChart:
    encode_x = alt.X(f"{x}:N", title=None, sort=None, axis=alt.Axis(labelAngle=-30, labelLimit=200))
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
            y=alt.Y("mean:Q", title=y_title, scale=alt.Scale(domain=[0, 1]) if unit_scale else alt.Undefined),
            color=color_encoding,
            tooltip=tooltip,
        )
    )
    errors = (
        alt.Chart(data)
        .mark_rule(color="#0F1B33")
        .encode(x=encode_x, xOffset=offset, y="lo:Q", y2="hi:Q")
    )
    return alt.layer(bars, errors).properties(height=height, title=title)


def render_consensus_tab() -> None:
    runs = load_consensus_runs()

    st.markdown("### Learning by Consensus")

    if runs.empty:
        st.info(
            "No completed Consensus benchmark yet. Run one from the "
            "Simulation page (several seeds give error bars)."
        )
        return

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    # Toggle buttons: every option stays visible, so a removed dataset can
    # always be switched back on with one click.
    datasets = sorted(runs["dataset"].unique())
    chosen_datasets = st.pills(
        "Datasets", datasets, selection_mode="multi", default=datasets,
        key="consensus_filter_datasets",
    ) or []
    filter_columns = st.columns([2, 2, 1])
    learners = sorted(runs["learner"].unique())
    chosen_learners = filter_columns[0].pills(
        "ILP system", learners, selection_mode="multi", default=learners,
        format_func=str.title, key="consensus_filter_learners",
    ) or []
    partitions = sorted(runs["partition"].unique())
    chosen_partitions = filter_columns[1].pills(
        "Partition", partitions, selection_mode="multi", default=partitions,
        format_func=lambda key: "IID" if key == "iid" else "Non-IID" if key == "non_iid" else key,
        key="consensus_filter_partitions",
    ) or []
    metric = filter_columns[2].selectbox(
        "Metric", list(METRICS), format_func=lambda m: METRICS[m]
    )

    frame = runs[
        runs["dataset"].isin(chosen_datasets)
        & runs["learner"].isin(chosen_learners)
        & runs["partition"].isin(chosen_partitions)
    ]
    if frame.empty:
        st.info("No run matches these filters.")
        return

    frame = frame.copy()
    frame["group"] = frame["dataset"] + " · " + frame["learner"]
    frame["bar"] = frame["group"] + " · " + frame["setting"]

    baseline_rows = int(frame[f"baseline_{metric}"].notna().sum())
    st.caption(
        f"{len(frame)} completed runs. Bars show the mean over runs (seeds) and the "
        "standard error. "
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
            "Most settings have fewer than 3 runs: error bars and p-values need "
            "several seeds (set “Runs” to 5–10 in the Simulation page)."
        )

    # ------------------------------------------------------------------
    # Figure 1 — predictive performance
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            f"**Figure 1 — Predictive performance ({METRICS[metric].lower()}).** "
            "The consensus next to its own members and to the centralized baseline."
        )
        pieces = []
        for label, column in (
            ("Consensus", f"consensus_{metric}"),
            ("Mean of the H_i", f"mean_h_{metric}"),
            ("Best H_i", f"best_h_{metric}"),
            (CENTRALIZED_LABEL, f"baseline_{metric}"),
        ):
            aggregated = _aggregate(frame.dropna(subset=[column]), ["bar"], column)
            if aggregated.empty:
                continue
            aggregated["series"] = label
            pieces.append(aggregated)
        figure_one = pd.concat(pieces, ignore_index=True)
        st.altair_chart(
            _bars_with_error(figure_one, "bar", "series", "", SERIES, METRICS[metric]),
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

    federated = frame[frame["k"] > 1]

    # ------------------------------------------------------------------
    # Figure 2 — does the vote help?
    # ------------------------------------------------------------------
    if not federated.empty:
        with st.container(border=True):
            st.markdown(
                "**Figure 2 — What the vote adds.** For each run: the consensus minus the "
                "mean of its hypotheses. Above 0, the vote beats the average member."
            )
            gain = federated.copy()
            gain["gain"] = gain[f"consensus_{metric}"] - gain[f"mean_h_{metric}"]
            gain["gain_best"] = gain[f"consensus_{metric}"] - gain[f"best_h_{metric}"]
            points = (
                alt.Chart(gain)
                .mark_circle(size=80, color=PURPLE, opacity=0.8)
                .encode(
                    x=alt.X("bar:N", title=None, axis=alt.Axis(labelAngle=-30, labelLimit=200)),
                    y=alt.Y("gain:Q", title=f"Consensus − mean H_i ({METRICS[metric]})"),
                    tooltip=["bar", alt.Tooltip("gain:Q", format=".3f"), "seed"],
                )
            )
            zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#8A93A3", strokeDash=[4, 4]).encode(y="y:Q")
            st.altair_chart((zero + points).properties(height=280), use_container_width=True)
            st.caption(
                "Share of runs where the consensus is at least as good as the best single "
                f"hypothesis: {(gain['gain_best'] >= 0).mean():.0%}."
            )

    # ------------------------------------------------------------------
    # Figure 3 — complexity
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            "**Figure 3 — Size of the learned theories.** Rules per hypothesis and body "
            "literals per rule, for each client hypothesis and for the centralized learner."
        )
        complexity_columns = st.columns(2)
        complexity_series = {"Consensus (per hypothesis)": PURPLE, CENTRALIZED_LABEL: RED}
        for column, key, base_key, title in (
            (complexity_columns[0], "rules_per_hypothesis", "baseline_rules", "Rules per hypothesis"),
            (complexity_columns[1], "body_literals", "baseline_body", "Body literals per rule"),
        ):
            parts = []
            for label, source in (
                ("Consensus (per hypothesis)", key),
                (CENTRALIZED_LABEL, base_key),
            ):
                part = _aggregate(frame.dropna(subset=[source]), ["bar"], source)
                if not part.empty:
                    part["series"] = label
                    parts.append(part)
            aggregated = pd.concat(parts, ignore_index=True)
            column.altair_chart(
                _bars_with_error(
                    aggregated, "bar", "series", title, complexity_series,
                    y_title=title, height=280, unit_scale=False,
                ),
                use_container_width=True,
            )
        st.caption(
            "Empty hypotheses count as 0 rules. A client that finds no rule in time "
            f"votes “negative”: {int(frame['n_empty'].sum())} empty hypotheses in the "
            "selected runs."
        )

    # ------------------------------------------------------------------
    # Figure 4 — number of clients
    # ------------------------------------------------------------------
    scaling_partitions = sorted(federated["partition"].unique()) if not federated.empty else []
    if frame["k"].nunique() > 1:
        with st.container(border=True):
            st.markdown("**Figure 4 — Effect of the number of clients.** The point at 1 client is the centralized baseline.")
            partition_choice = (
                st.selectbox("Partition", scaling_partitions, key="consensus_scaling_partition")
                if scaling_partitions
                else None
            )
            scaling = frame[(frame["k"] == 1) | (frame["partition"] == partition_choice)].copy()
            # Linked centralized baselines count as the k = 1 point.
            linked = frame[frame[f"baseline_{metric}"].notna() & (frame["k"] > 1)].copy()
            if not linked.empty:
                linked["k"] = 1
                linked[f"consensus_{metric}"] = linked[f"baseline_{metric}"]
                scaling = pd.concat([scaling, linked], ignore_index=True)
            aggregated = _aggregate(scaling, ["group", "k"], f"consensus_{metric}")
            line = (
                alt.Chart(aggregated)
                .mark_line(point=True)
                .encode(
                    x=alt.X("k:O", title="Number of clients"),
                    y=alt.Y("mean:Q", title=METRICS[metric], scale=alt.Scale(domain=[0, 1])),
                    color=alt.Color("group:N", title=None, scale=alt.Scale(range=PALETTE), legend=alt.Legend(orient="bottom")),
                    tooltip=["group", "k", alt.Tooltip("mean:Q", format=".3f"), alt.Tooltip("se:Q", format=".3f")],
                )
            )
            bands = (
                alt.Chart(aggregated)
                .mark_errorbar()
                .encode(x="k:O", y=alt.Y("lo:Q", title=""), y2="hi:Q", color=alt.Color("group:N", scale=alt.Scale(range=PALETTE), legend=None))
            )
            st.altair_chart((line + bands).properties(height=300), use_container_width=True)

    # ------------------------------------------------------------------
    # Figure 5 — IID vs label imbalance
    # ------------------------------------------------------------------
    if not federated.empty and federated["partition"].nunique() > 1:
        with st.container(border=True):
            st.markdown(
                "**Figure 5 — IID or label imbalance.** “non_iid” here means unbalanced class "
                "proportions between clients, not a different feature distribution."
            )
            aggregated = _aggregate(
                federated.assign(k_group=federated["group"] + " (k=" + federated["k"].astype(str) + ")"),
                ["k_group", "partition"],
                f"consensus_{metric}",
            )
            st.altair_chart(
                _bars_with_error(
                    aggregated,
                    "k_group",
                    "partition",
                    "",
                    {"iid": NAVY, "non_iid": RED},
                    METRICS[metric],
                ),
                use_container_width=True,
            )

    # ------------------------------------------------------------------
    # Figure 6 — cost
    # ------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            "**Figure 6 — Cost.** Learning time (clients learn in parallel, so the slowest "
            "client sets the time) and the size of the messages exchanged."
        )
        cost_columns = st.columns(2)
        time_parts = []
        for label, source in (
            ("Consensus (slowest client)", "time_slowest"),
            (CENTRALIZED_LABEL, "baseline_time"),
        ):
            part = _aggregate(frame.dropna(subset=[source]), ["bar"], source)
            if not part.empty:
                part["series"] = label
                time_parts.append(part)
        if time_parts:
            cost_columns[0].altair_chart(
                _bars_with_error(
                    pd.concat(time_parts, ignore_index=True), "bar", "series",
                    "Learning time (s)",
                    {"Consensus (slowest client)": TEAL, CENTRALIZED_LABEL: RED},
                    y_title="Seconds", height=280, unit_scale=False,
                ),
                use_container_width=True,
            )
        size_frame = federated.dropna(subset=["upload_kb"]) if not federated.empty else federated
        if not size_frame.empty:
            long = size_frame.melt(
                id_vars=["bar"],
                value_vars=["upload_kb", "ensemble_kb"],
                var_name="message",
                value_name="kb",
            )
            long["message"] = long["message"].map(
                {"upload_kb": "Hypotheses to the server", "ensemble_kb": "Ensemble to each client"}
            )
            by_bar = long.groupby(["bar", "message"], as_index=False)["kb"].mean()
            cost_columns[1].altair_chart(
                alt.Chart(by_bar)
                .mark_bar()
                .encode(
                    x=alt.X("bar:N", title=None, axis=alt.Axis(labelAngle=-30, labelLimit=200)),
                    y=alt.Y("kb:Q", title="KB"),
                    color=alt.Color(
                        "message:N",
                        title=None,
                        scale=alt.Scale(
                            domain=["Hypotheses to the server", "Ensemble to each client"],
                            range=[PURPLE, PINK],
                        ),
                        legend=alt.Legend(orient="bottom", symbolType="circle"),
                    ),
                    tooltip=["bar", "message", alt.Tooltip("kb:Q", format=".2f")],
                )
                .properties(height=280, title="Messages exchanged"),
                use_container_width=True,
            )

    # ------------------------------------------------------------------
    # Figure 7 — agreement between the hypotheses of one run
    # ------------------------------------------------------------------
    if not federated.empty:
        with st.container(border=True):
            st.markdown(
                "**Figure 7 — Agreement inside one run.** Share of test examples on which two "
                "hypotheses give the same answer. The “Truth” column is each hypothesis' accuracy: "
                "the vote helps when the hypotheses are right on different examples."
            )
            options = federated.sort_values("experiment_id", ascending=False)
            labels = {
                int(row.experiment_id): f"#{int(row.experiment_id)} · {row.bar} · seed {row.seed}"
                for row in options.itertuples()
            }
            chosen = st.selectbox(
                "Run",
                list(labels),
                format_func=lambda key: labels[key],
                key="consensus_agreement_run",
            )
            matrix = agreement_matrix(load_vote_traces(int(chosen)))
            if matrix.empty:
                st.info("No vote traces for this run.")
            else:
                long = matrix.reset_index().melt(id_vars="index", var_name="other", value_name="share")
                long = long.rename(columns={"index": "row"})
                order = list(matrix.index)
                heat = (
                    alt.Chart(long)
                    .mark_rect()
                    .encode(
                        x=alt.X("other:N", sort=order, title=None),
                        y=alt.Y("row:N", sort=order, title=None),
                        color=alt.Color("share:Q", scale=alt.Scale(domain=[0, 1], range=["#F3F4F6", PURPLE]), legend=None),
                        tooltip=["row", "other", alt.Tooltip("share:Q", format=".2f")],
                    )
                )
                text = (
                    alt.Chart(long)
                    .mark_text()
                    .encode(
                        x=alt.X("other:N", sort=order),
                        y=alt.Y("row:N", sort=order),
                        text=alt.Text("share:Q", format=".2f"),
                        color=alt.condition(alt.datum.share > 0.55, alt.value("#FFFFFF"), alt.value("#0F1B33")),
                    )
                )
                st.altair_chart((heat + text).properties(height=260), use_container_width=True)

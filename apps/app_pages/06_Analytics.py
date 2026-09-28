from __future__ import annotations

import sys
from pathlib import Path
from typing import get_args

import altair as alt
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_connection
from core.experiment import Approach as _Approach

# Canonical list of every approach the platform supports (not just the ones
# that happen to have a recorded benchmark yet), so e.g. "coordination" is
# selectable in the filter even before its first benchmark run exists.
ALL_APPROACHES = list(get_args(_Approach))


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Analytics | FILP",
    page_icon=":material/monitoring:",
    layout="wide",
)

if hasattr(st, "logo"):
    try:
        st.logo(str(PROJECT_ROOT / "assets" / "filp_wordmark_white.svg"), size="large")
    except Exception:
        pass




# ---------------------------------------------------------------------
# Visual design system — same palette/classes as the other pages.
# ---------------------------------------------------------------------

PALETTE = {
    "bg_card": "#F6F8FC",
    "border": "#E2E8F5",
    "text_muted": "#5B6472",
    "text": "#1F2430",
    "primary": "#5B7FDE",
    "primary_soft": "#EAF0FE",
    "success": "#2F9E63",
    "success_soft": "#E7F6EE",
    "neutral": "#8A93A3",
    "neutral_soft": "#EEF1F6",
}

CHART_COLORS = ["#5B7FDE", "#7FB88F", "#E8A85C", "#C97BB0", "#6BB6C9", "#B99BD8"]


def inject_style() -> None:
    st.markdown(
        f"""
        <style>
        .block-container {{
            padding-top: 3rem;
            padding-bottom: 3rem;
            padding-left: 2.2rem;
            padding-right: 2.2rem;
            max-width: 100% !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 14px !important;
        }}

        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin: 4px 0 8px 0;
        }}
        .metric-card {{
            background: {PALETTE["bg_card"]};
            border: 1px solid {PALETTE["border"]};
            border-radius: 12px;
            padding: 14px 16px;
        }}
        .metric-card .metric-label {{
            font-size: 0.78rem;
            color: {PALETTE["text_muted"]};
            font-weight: 500;
            margin-bottom: 4px;
        }}
        .metric-card .metric-value {{
            font-size: 1.35rem;
            color: {PALETTE["text"]};
            font-weight: 600;
            line-height: 1.2;
        }}

        .section-title {{
            font-size: 1.05rem;
            font-weight: 600;
            color: {PALETTE["text"]};
            margin: 6px 0 2px 0;
        }}
        .section-caption {{
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 10px;
        }}
        .breadcrumb {{
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 4px;
        }}

        .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 14px 0; }}
        .chip {{ border-radius: 999px; padding: 4px 12px; font-size: 0.8rem; font-weight: 500; }}
        .chip-neutral {{ background: {PALETTE["neutral_soft"]}; color: {PALETTE["text"]}; }}
        .chip-primary {{ background: {PALETTE["primary_soft"]}; color: {PALETTE["primary"]}; }}

        /* --------------------------------------------------------- */
        /* Dark navy sidebar, matching the Experiments page          */
        /* --------------------------------------------------------- */

        section[data-testid="stSidebar"] {{
            background: #0F1B33 !important;
            border-right: 1px solid #22314F;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{
            height: auto !important;
            min-height: 0 !important;
            margin-bottom: 4px !important;
            padding-top: 6px !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] img,
        section[data-testid="stSidebar"] [data-testid="stLogo"] {{
            height: 76px !important;
            max-height: none !important;
            width: auto !important;
            max-width: 100% !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {{
            display: none !important;
        }}
        section[data-testid="stSidebar"] > div:first-child {{
            min-height: 100vh !important;
            display: flex !important;
            flex-direction: column !important;
        }}
        [data-testid="stSidebarNav"] {{
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 auto !important;
            min-height: 0 !important;
        }}
        [data-testid="stSidebarNavItems"] {{
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 auto !important;
        }}
        [data-testid="stSidebarNavItems"] li:nth-last-of-type(2) {{
            margin-top: auto !important;
            padding-top: 303px;
            border-top: 1px solid #22314F;
        }}
        section[data-testid="stSidebar"] * {{
            color: #C7D2EC !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{
            border-radius: 10px;
            margin: 2px 8px 2px 0 !important;
            padding: 8px 8px 8px 4px !important;
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a > span:first-child {{
            margin: 0 !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            flex-shrink: 0 !important;
            width: auto !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a [data-testid="stIconMaterial"] {{
            width: 27px !important;
            height: 27px !important;
            min-width: 27px !important;
            font-size: 27px !important;
            margin: 0 !important;
            padding: 0 !important;
            color: #E4EAFB !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a > span:last-child {{
            font-size: 18px !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] [data-testid="stIconMaterial"] {{
            color: #FFFFFF !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {{
            background: #1B2A4C !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: #1B2A4C !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] * {{
            color: #FFFFFF !important;
            font-weight: 600;
        }}
        section[data-testid="stSidebar"] hr {{
            border-color: #22314F !important;
        }}
        section[data-testid="stSidebar"] .stButton button {{
            background: {PALETTE["primary"]} !important;
            color: #FFFFFF !important;
            border: none !important;
        }}
        section[data-testid="stSidebar"] input {{
            background: #1B2A4C !important;
            color: #FFFFFF !important;
            border-color: #22314F !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_grid(items: list[dict]) -> None:
    card_parts = []
    for item in items:
        card_parts.append(
            '<div class="metric-card">'
            f'<div class="metric-label">{item["label"]}</div>'
            f'<div class="metric-value">{item["value"]}</div>'
            "</div>"
        )
    st.markdown(f'<div class="metric-grid">{"".join(card_parts)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------

# Metrics that can be compared/plotted, and how to label them.
METRICS = {
    "learning_time_seconds": "Learning time (s)",
    "total_time_seconds": "End-to-end time (s)",
    "number_of_rounds": "Rounds",
    "number_of_programs": "Programs explored",
    "final_score": "Final score",
}

GROUP_COLUMNS = ["approach", "dataset", "number_of_clients", "partition_strategy"]


@st.cache_data(ttl=30)
def load_all_run_results() -> pd.DataFrame:
    """One row per (benchmark, run) with its server-side metrics."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                b.id AS benchmark_id,
                b.name AS benchmark_name,
                b.approach,
                b.dataset,
                b.number_of_clients,
                b.partition_strategy,
                b.status AS benchmark_status,
                br.experiment_id,
                br.run_number,
                sr.learning_time_seconds,
                sr.total_time_seconds,
                sr.startup_time_seconds,
                sr.popper_time_seconds,
                sr.federation_time_seconds,
                sr.number_of_rounds,
                sr.number_of_programs,
                sr.final_score,
                sr.tp,
                sr.fn,
                sr.tn,
                sr.fp,
                COALESCE(ce.client_eval_wall, 0.0) AS client_eval_wall
            FROM benchmarks AS b
            JOIN benchmark_runs AS br
                ON br.benchmark_id = b.id
            JOIN experiments AS e
                ON e.id = br.experiment_id
            LEFT JOIN server_results AS sr
                ON sr.experiment_id = e.id
            LEFT JOIN (
                SELECT experiment_id, MAX(total_eval_wall_seconds) AS client_eval_wall
                FROM client_results
                GROUP BY experiment_id
            ) AS ce
                ON ce.experiment_id = e.id
            """
        ).fetchall()

    df = pd.DataFrame([dict(row) for row in rows])
    if df.empty:
        return df

    # Popper's raw server-side timer (popper_time_seconds, aka Tcentral)
    # only covers the server's own build/ground/add work; the client-side
    # coverage testing of each proposed program (client_eval_wall) is real
    # Popper work too, just executed remotely — see the correction applied
    # in core.benchmark_results.load_benchmark_summary for the same logic,
    # including why this is a MAX across clients and not a SUM (clients
    # evaluate in parallel, so the server only waits for the slowest one).
    df["popper_core_seconds"] = df["popper_time_seconds"].fillna(0.0)
    df["total_popper_time_seconds"] = df["popper_core_seconds"] + df["client_eval_wall"]
    df["federation_overhead_seconds"] = (
        df["federation_time_seconds"].fillna(0.0) - df["client_eval_wall"]
    ).clip(lower=0.0)

    return df


@st.cache_data(ttl=30)
def load_client_and_consensus(experiment_ids: tuple[int, ...]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-client federated breakdown and consensus result for a set of
    experiment ids — fetched on demand (only once a benchmark row is
    selected for drill-down), rather than joined into the main query."""

    if not experiment_ids:
        return pd.DataFrame(), pd.DataFrame()

    placeholders = ",".join("?" for _ in experiment_ids)

    with get_connection() as connection:
        client_rows = connection.execute(
            f"""
            SELECT
                experiment_id, client_id, dataset_partition,
                number_of_examples, number_of_positive_examples, number_of_negative_examples,
                average_eval_wall_seconds, accepted_solution, final_score,
                tp, fn, tn, fp
            FROM client_results
            WHERE experiment_id IN ({placeholders})
            ORDER BY experiment_id, client_id
            """,
            experiment_ids,
        ).fetchall()

        consensus_rows = connection.execute(
            f"""
            SELECT
                experiment_id, learner, number_of_clients, number_of_hypotheses,
                hypotheses, accuracy, precision, recall, f1
            FROM consensus_results
            WHERE experiment_id IN ({placeholders})
            """,
            experiment_ids,
        ).fetchall()

    return (
        pd.DataFrame([dict(row) for row in client_rows]),
        pd.DataFrame([dict(row) for row in consensus_rows]),
    )


def latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "±": r"$\pm$",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def to_latex_table(display_df: pd.DataFrame, caption: str, label: str) -> str:
    # Built by hand (booktabs style) instead of pandas.to_latex(), which
    # pulls in jinja2 via pandas' Styler and can break on older jinja2
    # versions — plain string formatting has no extra dependency.
    columns = list(display_df.columns)
    column_spec = "l" * len(columns)

    header = " & ".join(latex_escape(col) for col in columns) + r" \\"
    body_lines = [
        " & ".join(latex_escape(value) for value in row) + r" \\"
        for row in display_df.itertuples(index=False, name=None)
    ]

    lines = [
        r"\begin{table}[ht]",
        r"\centering",
        f"\\begin{{tabular}}{{{column_spec}}}",
        r"\toprule",
        header,
        r"\midrule",
        *body_lines,
        r"\bottomrule",
        r"\end{tabular}",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        r"\end{table}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------
# Page body
# ---------------------------------------------------------------------

inject_style()

st.markdown('<div class="breadcrumb">Home &gt; Analytics</div>', unsafe_allow_html=True)

st.title("Analytics")
st.caption(
    "Compare experiments and benchmarks by dataset, number of clients, "
    "partition strategy and approach, with mean ± std across runs."
)

raw_df = load_all_run_results()

if raw_df.empty:
    st.info("No benchmark has been recorded yet. Run one from the Experiments page first.")
    st.stop()

# --- Filters -------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="section-title">Filters</div>', unsafe_allow_html=True)

    only_completed = st.checkbox(
        "Only completed benchmarks",
        value=True,
        help="Excludes benchmarks that are still running or failed, so partial results don't skew the averages.",
    )

    working_df = raw_df.copy()
    if only_completed:
        working_df = working_df[working_df["benchmark_status"] == "COMPLETED"]

    filter_columns = st.columns(4)

    with filter_columns[0]:
        # Always offer every known approach (not just the ones with a
        # recorded benchmark yet) so e.g. "coordination" is selectable as
        # soon as it's run, without needing a code change to appear here.
        present_approaches = set(working_df["approach"].dropna().unique().tolist())
        approach_options = ALL_APPROACHES + sorted(present_approaches - set(ALL_APPROACHES))
        selected_approaches = st.multiselect(
            "Approach",
            options=approach_options,
            default=[a for a in approach_options if a in present_approaches],
            help="Every approach the platform supports is listed, even ones with no recorded benchmark yet.",
        )

    with filter_columns[1]:
        dataset_options = sorted(working_df["dataset"].dropna().unique().tolist())
        selected_datasets = st.multiselect("Dataset", options=dataset_options, default=dataset_options)

    with filter_columns[2]:
        k_options = sorted(working_df["number_of_clients"].dropna().unique().tolist())
        selected_k = st.multiselect("Number of clients (K)", options=k_options, default=k_options)

    with filter_columns[3]:
        partition_options = sorted(working_df["partition_strategy"].dropna().unique().tolist())
        selected_partitions = st.multiselect("Partition", options=partition_options, default=partition_options)

working_df = working_df[
    working_df["approach"].isin(selected_approaches)
    & working_df["dataset"].isin(selected_datasets)
    & working_df["number_of_clients"].isin(selected_k)
    & working_df["partition_strategy"].isin(selected_partitions)
]

if working_df.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# Same "config" label used for grouping, computed here too so individual
# raw rows can be matched against a selection made on the aggregated chart.
working_df = working_df.copy()
working_df["config"] = (
    working_df["approach"] + " · " + working_df["dataset"]
    + " · K=" + working_df["number_of_clients"].astype(str)
    + " · " + working_df["partition_strategy"]
)

st.write("")

render_metric_grid(
    [
        {"label": "Configurations", "value": working_df.groupby(GROUP_COLUMNS).ngroups},
        {"label": "Benchmarks", "value": working_df["benchmark_id"].nunique()},
        {"label": "Runs", "value": len(working_df)},
    ]
)

st.divider()

# --- Compare configurations ----------------------------------------------

st.markdown('<div class="section-title">Compare configurations</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-caption">Mean ± standard deviation pooled across every run that matches a configuration — '
    'click a bar to drill down into its individual runs below</div>',
    unsafe_allow_html=True,
)

aggregated = (
    working_df.groupby(GROUP_COLUMNS)[list(METRICS.keys())]
    .agg(["mean", "std", "count"])
)
aggregated.columns = ["_".join(col) for col in aggregated.columns]
aggregated = aggregated.reset_index()
aggregated["config"] = (
    aggregated["approach"] + " · " + aggregated["dataset"]
    + " · K=" + aggregated["number_of_clients"].astype(str)
    + " · " + aggregated["partition_strategy"]
)

metric_key = st.selectbox(
    "Metric to compare",
    options=list(METRICS.keys()),
    format_func=lambda key: METRICS[key],
)

chart_df = aggregated.rename(
    columns={f"{metric_key}_mean": "mean", f"{metric_key}_std": "std", f"{metric_key}_count": "n"}
)[["config", "approach", "mean", "std", "n"]].dropna(subset=["mean"])

selected_configs: list[str] = []

if chart_df.empty:
    st.info(f"No data available yet for {METRICS[metric_key]}.")
else:
    config_select = alt.selection_point(fields=["config"], name="config_select", empty=True, toggle=True)

    bars = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("config:N", title=None, sort=None, axis=alt.Axis(labelAngle=-30)),
            y=alt.Y("mean:Q", title=METRICS[metric_key]),
            color=alt.Color("approach:N", title=None, scale=alt.Scale(range=CHART_COLORS)),
            opacity=alt.condition(config_select, alt.value(1.0), alt.value(0.35)),
            tooltip=["config", "mean", "std", "n"],
        )
        .add_params(config_select)
    )
    error_bars = (
        alt.Chart(chart_df)
        .mark_errorbar()
        .encode(
            x=alt.X("config:N", title=None, sort=None),
            y=alt.Y("mean:Q", title=METRICS[metric_key]),
            yError="std:Q",
        )
    )
    chart = (
        (bars + error_bars)
        .properties(height=320)
        .configure_axis(grid=False, domainColor=PALETTE["border"], labelColor=PALETTE["text_muted"])
        .configure_view(strokeWidth=0)
    )
    chart_event = st.altair_chart(
        chart,
        use_container_width=True,
        on_select="rerun",
        key="config_compare_chart",
    )

    if chart_event and "selection" in chart_event:
        selected_configs = sorted(
            {
                point["config"]
                for point in chart_event["selection"].get("config_select", [])
                if "config" in point
            }
        )

st.write("")

# --- Drill down into the selected configuration(s) -----------------------

if selected_configs:
    drill_df = working_df[working_df["config"].isin(selected_configs)].copy()

    with st.container(border=True):
        st.markdown(
            f'<div class="section-title">Drill down — {", ".join(selected_configs)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-caption">Every individual run behind the selected bar(s) — '
            'useful to see whether the mean hides a lot of variance</div>',
            unsafe_allow_html=True,
        )

        strip = (
            alt.Chart(drill_df)
            .mark_circle(size=90, opacity=0.75)
            .encode(
                x=alt.X("benchmark_name:N", title=None, axis=alt.Axis(labelAngle=-30)),
                y=alt.Y(f"{metric_key}:Q", title=METRICS[metric_key]),
                color=alt.Color("config:N", title=None, scale=alt.Scale(range=CHART_COLORS)),
                tooltip=["benchmark_name", "run_number", metric_key],
            )
            .properties(height=260)
            .configure_axis(grid=False, domainColor=PALETTE["border"], labelColor=PALETTE["text_muted"])
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(strip, use_container_width=True)

        drill_display = drill_df[
            ["benchmark_name", "run_number", *METRICS.keys()]
        ].rename(columns={"benchmark_name": "Benchmark", "run_number": "Run", **METRICS})
        st.dataframe(drill_display, use_container_width=True, hide_index=True)
else:
    st.caption("No bar selected — click one above to drill into its individual runs.")

st.write("")

# Human-readable "mean ± std (n=..)" columns for display and export.
display_df = aggregated[["config", "approach", "dataset", "number_of_clients", "partition_strategy"]].copy()
display_df.columns = ["Configuration", "Approach", "Dataset", "K", "Partition"]

for key, label in METRICS.items():
    means = aggregated[f"{key}_mean"]
    stds = aggregated[f"{key}_std"].fillna(0.0)
    counts = aggregated[f"{key}_count"]
    display_df[label] = [
        f"{m:.3f} ± {s:.3f} (n={int(n)})" if pd.notna(m) else "—"
        for m, s, n in zip(means, stds, counts)
    ]

st.dataframe(display_df, use_container_width=True, hide_index=True)

export_left, export_right = st.columns(2)

with export_left:
    st.download_button(
        "Download comparison as CSV",
        data=display_df.to_csv(index=False).encode("utf-8"),
        file_name="filp_configuration_comparison.csv",
        mime="text/csv",
        use_container_width=True,
    )

with export_right:
    latex_source = to_latex_table(
        display_df,
        caption="Comparison of FILP configurations (mean $\\pm$ std across runs).",
        label="tab:filp-configurations",
    )
    st.download_button(
        "Download comparison as LaTeX",
        data=latex_source.encode("utf-8"),
        file_name="filp_configuration_comparison.tex",
        mime="text/plain",
        use_container_width=True,
    )

with st.expander("Preview LaTeX source"):
    st.code(latex_source, language="latex")

st.divider()

# --- Timing breakdown by method -------------------------------------------

TIMING_COMPONENTS = {
    "client_eval_wall": "Client evaluation time (slowest client)",
    "popper_core_seconds": "Popper core (Tcentral, server-side)",
    "total_popper_time_seconds": "Total Popper time (core + client eval)",
    "federation_overhead_seconds": "Federation overhead (pure communication)",
}

st.markdown('<div class="section-title">Timing breakdown by method</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-caption">Pick one approach and see, dataset by dataset, how its total time '
    'splits between client-side evaluation, the server\'s own Popper search, and pure federation overhead</div>',
    unsafe_allow_html=True,
)

timing_approach_options = [a for a in ALL_APPROACHES if a in present_approaches]
if not timing_approach_options:
    st.info("No approach with recorded runs yet.")
else:
    timing_approach = st.selectbox("Approach", options=timing_approach_options, key="timing_breakdown_approach")

    timing_df = working_df[working_df["approach"] == timing_approach].copy()

    if timing_df.empty:
        st.info(f"No completed runs recorded yet for {timing_approach}.")
    else:
        long_rows = []
        for dataset, group in timing_df.groupby("dataset"):
            for column, label in TIMING_COMPONENTS.items():
                values = group[column].dropna().tolist()
                if not values:
                    continue
                long_rows.append(
                    {
                        "dataset": dataset,
                        "metric": label,
                        "mean": sum(values) / len(values),
                        "std": pd.Series(values).std(ddof=0) if len(values) > 1 else 0.0,
                        "n": len(values),
                    }
                )
        timing_long_df = pd.DataFrame(long_rows)

        if timing_long_df.empty:
            st.info(f"No timing data recorded yet for {timing_approach}.")
        else:
            timing_chart = (
                alt.Chart(timing_long_df)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("dataset:N", title=None, axis=alt.Axis(labelAngle=-30)),
                    xOffset=alt.XOffset("metric:N", sort=list(TIMING_COMPONENTS.values())),
                    y=alt.Y("mean:Q", title="Seconds"),
                    color=alt.Color(
                        "metric:N",
                        title=None,
                        sort=list(TIMING_COMPONENTS.values()),
                        scale=alt.Scale(range=CHART_COLORS),
                    ),
                    tooltip=["dataset", "metric", "mean", "std", "n"],
                )
                .properties(height=320)
                .configure_axis(grid=False, domainColor=PALETTE["border"], labelColor=PALETTE["text_muted"])
                .configure_view(strokeWidth=0)
                .configure_legend(orient="bottom", title=None)
            )
            st.altair_chart(timing_chart, use_container_width=True)

            timing_table = timing_long_df.pivot(index="dataset", columns="metric", values="mean").reset_index()
            timing_table.columns = ["Dataset"] + [str(c) for c in timing_table.columns[1:]]
            for col in timing_table.columns[1:]:
                timing_table[col] = timing_table[col].map(lambda v: f"{v:.3f} s" if pd.notna(v) else "—")
            st.dataframe(timing_table, use_container_width=True, hide_index=True)

            st.caption(
                "Total Popper time = Popper core + client evaluation. Federation overhead is what's left of "
                "the federated round-trip once client evaluation is excluded — pure broadcast/aggregation cost."
            )

st.divider()

# --- Per-benchmark detail --------------------------------------------------

st.markdown('<div class="section-title">Per-benchmark detail</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-caption">One row per benchmark — select a row to see its federated client '
    'breakdown and consensus hypothesis, if any</div>',
    unsafe_allow_html=True,
)

benchmark_group_columns = ["benchmark_id", "benchmark_name", *GROUP_COLUMNS]
benchmark_level = (
    working_df.groupby(benchmark_group_columns)[list(METRICS.keys())]
    .agg(["mean", "std", "count"])
)
benchmark_level.columns = ["_".join(col) for col in benchmark_level.columns]
benchmark_level = benchmark_level.reset_index()

benchmark_display_df = benchmark_level[
    ["benchmark_id", "benchmark_name", *GROUP_COLUMNS]
].copy()
benchmark_display_df.columns = ["ID", "Name", "Approach", "Dataset", "K", "Partition"]

for key, label in METRICS.items():
    means = benchmark_level[f"{key}_mean"]
    stds = benchmark_level[f"{key}_std"].fillna(0.0)
    counts = benchmark_level[f"{key}_count"]
    benchmark_display_df[label] = [
        f"{m:.3f} ± {s:.3f} (n={int(n)})" if pd.notna(m) else "—"
        for m, s, n in zip(means, stds, counts)
    ]

benchmark_selection = st.dataframe(
    benchmark_display_df,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    key="benchmark_detail_table",
)

st.download_button(
    "Download per-benchmark table as CSV",
    data=benchmark_display_df.to_csv(index=False).encode("utf-8"),
    file_name="filp_benchmarks.csv",
    mime="text/csv",
)

# --- Federated / consensus drill-down for the selected benchmark ---------

selected_rows = []
if benchmark_selection and "selection" in benchmark_selection:
    selected_rows = benchmark_selection["selection"].get("rows", [])

if selected_rows:
    picked_benchmark_id = int(benchmark_display_df.iloc[selected_rows[0]]["ID"])
    picked_benchmark_name = benchmark_display_df.iloc[selected_rows[0]]["Name"]
    experiment_ids = tuple(
        int(x)
        for x in working_df.loc[working_df["benchmark_id"] == picked_benchmark_id, "experiment_id"]
        .dropna()
        .unique()
        .tolist()
    )

    client_df, consensus_df = load_client_and_consensus(experiment_ids)

    with st.container(border=True):
        st.markdown(
            f'<div class="section-title">Benchmark detail — {picked_benchmark_name}</div>',
            unsafe_allow_html=True,
        )

        if client_df.empty and consensus_df.empty:
            st.caption(
                "No federated client results or consensus hypothesis recorded for this benchmark "
                "(expected for a centralized run)."
            )
        else:
            if not client_df.empty:
                st.markdown("**Per-client breakdown**")
                client_display = client_df.rename(
                    columns={
                        "experiment_id": "Run (experiment)",
                        "client_id": "Client",
                        "dataset_partition": "Partition",
                        "number_of_examples": "Examples",
                        "number_of_positive_examples": "Positive",
                        "number_of_negative_examples": "Negative",
                        "average_eval_wall_seconds": "Avg eval time (s)",
                        "accepted_solution": "Accepted solution",
                        "final_score": "Final score",
                    }
                )
                client_display["Accepted solution"] = client_display["Accepted solution"].map(
                    {1: "yes", 0: "no"}
                )
                st.dataframe(client_display, use_container_width=True, hide_index=True)

                eval_time_chart = (
                    alt.Chart(client_df)
                    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(
                        x=alt.X("client_id:N", title="Client"),
                        y=alt.Y("average_eval_wall_seconds:Q", title="Avg eval time (s)"),
                        color=alt.Color("experiment_id:N", title="Run", scale=alt.Scale(range=CHART_COLORS)),
                        tooltip=["experiment_id", "client_id", "average_eval_wall_seconds", "final_score"],
                    )
                    .properties(height=220)
                    .configure_axis(grid=False, domainColor=PALETTE["border"], labelColor=PALETTE["text_muted"])
                    .configure_view(strokeWidth=0)
                )
                st.altair_chart(eval_time_chart, use_container_width=True)

            if not consensus_df.empty:
                st.markdown("**Consensus hypothesis**")
                consensus_display = consensus_df.rename(
                    columns={
                        "experiment_id": "Run (experiment)",
                        "learner": "Learner",
                        "number_of_clients": "Clients",
                        "number_of_hypotheses": "Hypotheses proposed",
                        "hypotheses": "Hypotheses",
                        "accuracy": "Accuracy",
                        "precision": "Precision",
                        "recall": "Recall",
                        "f1": "F1",
                    }
                )
                st.dataframe(
                    consensus_display.drop(columns=["Hypotheses"]),
                    use_container_width=True,
                    hide_index=True,
                )
                for _, row in consensus_df.iterrows():
                    with st.expander(f"Hypothesis text — run {row['experiment_id']}"):
                        st.code(row["hypotheses"], language="prolog")
else:
    st.caption("Select a row above to see its federated client breakdown and consensus hypothesis.")

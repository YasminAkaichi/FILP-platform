from __future__ import annotations

import sys
from pathlib import Path

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


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Analytics | FILP",
    page_icon="",
    layout="wide",
)

LOGO_PATH = PROJECT_ROOT / "assets" / "filp_logo.svg"

if hasattr(st, "logo"):
    try:
        st.logo(str(LOGO_PATH), size="large")
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

        .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 14px 0; }}
        .chip {{ border-radius: 999px; padding: 4px 12px; font-size: 0.8rem; font-weight: 500; }}
        .chip-neutral {{ background: {PALETTE["neutral_soft"]}; color: {PALETTE["text"]}; }}
        .chip-primary {{ background: {PALETTE["primary_soft"]}; color: {PALETTE["primary"]}; }}
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
                br.run_number,
                sr.learning_time_seconds,
                sr.total_time_seconds,
                sr.number_of_rounds,
                sr.number_of_programs,
                sr.final_score
            FROM benchmarks AS b
            JOIN benchmark_runs AS br
                ON br.benchmark_id = b.id
            JOIN experiments AS e
                ON e.id = br.experiment_id
            LEFT JOIN server_results AS sr
                ON sr.experiment_id = e.id
            """
        ).fetchall()

    return pd.DataFrame([dict(row) for row in rows])


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
        approach_options = sorted(working_df["approach"].dropna().unique().tolist())
        selected_approaches = st.multiselect("Approach", options=approach_options, default=approach_options)

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
    '<div class="section-caption">Mean ± standard deviation pooled across every run that matches a configuration</div>',
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

if chart_df.empty:
    st.info(f"No data available yet for {METRICS[metric_key]}.")
else:
    bars = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("config:N", title=None, sort=None, axis=alt.Axis(labelAngle=-30)),
            y=alt.Y("mean:Q", title=METRICS[metric_key]),
            color=alt.Color("approach:N", title=None, scale=alt.Scale(range=CHART_COLORS)),
            tooltip=["config", "mean", "std", "n"],
        )
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
    st.altair_chart(chart, use_container_width=True)

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

# --- Per-benchmark detail --------------------------------------------------

st.markdown('<div class="section-title">Per-benchmark detail</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-caption">One row per benchmark — useful to spot a single run that skews a configuration\'s average</div>',
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

st.dataframe(benchmark_display_df, use_container_width=True, hide_index=True)

st.download_button(
    "Download per-benchmark table as CSV",
    data=benchmark_display_df.to_csv(index=False).encode("utf-8"),
    file_name="filp_benchmarks.csv",
    mime="text/csv",
)

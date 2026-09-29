from __future__ import annotations

import sys
from pathlib import Path
from typing import get_args

import altair as alt
import numpy as np
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
# that happen to have a recorded benchmark yet).
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
# Visual design system — aligned with 05_Experiments.py so both pages
# look like one product rather than two prototypes.
# ---------------------------------------------------------------------

PALETTE = {
    "bg_card": "#F6F8FC",
    "border": "#E2E8F5",
    "text_muted": "#5B6472",
    "text": "#1F2430",
    "primary": "#3E63DE",
    "primary_soft": "#EAF0FE",
    "success": "#2F9E63",
    "success_soft": "#E7F6EE",
    "warning": "#C98A1F",
    "warning_soft": "#FCF1DE",
    "error": "#D1554B",
    "error_soft": "#FBEAE8",
    "neutral": "#8A93A3",
    "neutral_soft": "#EEF1F6",
    "sidebar_bg": "#0F1B33",
    "sidebar_text": "#C7D2EC",
    "sidebar_text_muted": "#7C87A6",
    "sidebar_active_bg": "#1B2A4C",
    "sidebar_border": "#22314F",
}

CHART_COLORS = ["#3E63DE", "#7FB88F", "#E8A85C", "#C97BB0", "#6BB6C9", "#B99BD8"]

STATUS_STYLE = {
    "completed": (PALETTE["success"], PALETTE["success_soft"], "✓"),
    "success": (PALETTE["success"], PALETTE["success_soft"], "✓"),
    "running": (PALETTE["primary"], PALETTE["primary_soft"], "●"),
    "pending": (PALETTE["neutral"], PALETTE["neutral_soft"], "○"),
    "queued": (PALETTE["neutral"], PALETTE["neutral_soft"], "○"),
    "failed": (PALETTE["error"], PALETTE["error_soft"], "✕"),
    "error": (PALETTE["error"], PALETTE["error_soft"], "✕"),
}

# Same as 05_Experiments.py, plus "centralized" (a real 4th approach in the
# schema that the Experiments page currently leaves un-styled/neutral).
METHOD_STYLE = {
    "consensus": ("#7C5CFC", "#EFEAFE", "Consensus"),
    "collaboration": ("#3E7BFA", "#E8F0FE", "Collaboration"),
    "coordination": ("#E08A2B", "#FCEEDD", "Coordination"),
    "centralized": ("#2A9D8F", "#E3F5F3", "Centralized"),
}


def inject_style() -> None:
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-feature-settings: "tnum";
        }}

        .block-container {{
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            padding-top: 3rem;
            padding-bottom: 3rem;
            padding-left: 2.2rem;
            padding-right: 2.2rem;
            max-width: 100% !important;
        }}
        [data-testid="stHeader"] {{
            background: transparent;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            border-radius: 14px !important;
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
            letter-spacing: 0.01em;
            margin-bottom: 4px;
        }}
        .metric-card .metric-value {{
            font-size: 1.35rem;
            color: {PALETTE["text"]};
            font-weight: 600;
            line-height: 1.2;
        }}
        .metric-card .metric-sub {{
            font-size: 0.75rem;
            color: {PALETTE["text_muted"]};
            margin-top: 2px;
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
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
        .view-all-link {{
            font-size: 0.85rem;
            font-weight: 600;
            color: {PALETTE["primary"]};
        }}

        .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 14px 0; }}
        .chip {{ background: {PALETTE["neutral_soft"]}; color: {PALETTE["text"]}; border-radius: 999px; padding: 4px 12px; font-size: 0.8rem; font-weight: 500; }}
        .chip-neutral {{ background: {PALETTE["neutral_soft"]}; color: {PALETTE["text"]}; }}
        .chip-primary {{ background: {PALETTE["primary_soft"]}; color: {PALETTE["primary"]}; }}

        code, .stCode {{
            font-size: 0.82rem !important;
        }}

        button[data-baseweb="tab"] {{
            color: {PALETTE["text_muted"]} !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {PALETTE["primary"]} !important;
        }}
        div[data-baseweb="tab-highlight"] {{
            background-color: {PALETTE["primary"]} !important;
        }}
        div[data-baseweb="tab-border"] {{
            background-color: {PALETTE["border"]} !important;
        }}

        /* --------------------------------------------------------- */
        /* Dark navy sidebar, matching the Experiments page          */
        /* --------------------------------------------------------- */

        section[data-testid="stSidebar"] {{
            background: {PALETTE["sidebar_bg"]} !important;
            border-right: 1px solid {PALETTE["sidebar_border"]};
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
            color: {PALETTE["sidebar_text"]} !important;
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
            background: {PALETTE["sidebar_active_bg"]} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: {PALETTE["sidebar_active_bg"]} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] * {{
            color: #FFFFFF !important;
            font-weight: 600;
        }}
        section[data-testid="stSidebar"] hr {{
            border-color: {PALETTE["sidebar_border"]} !important;
        }}
        section[data-testid="stSidebar"] .stButton button {{
            background: {PALETTE["primary"]} !important;
            color: #FFFFFF !important;
            border: none !important;
        }}
        section[data-testid="stSidebar"] input {{
            background: {PALETTE["sidebar_active_bg"]} !important;
            color: #FFFFFF !important;
            border-color: {PALETTE["sidebar_border"]} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_badge(status: str | None) -> str:
    key = (status or "unknown").strip().lower()
    color, bg, dot = STATUS_STYLE.get(key, (PALETTE["neutral"], PALETTE["neutral_soft"], "○"))
    label = (status or "unknown").replace("_", " ").title()
    return f'<span class="badge" style="color:{color};background:{bg};">{dot} {label}</span>'


def render_method_badge(approach: str | None) -> str:
    key = (approach or "").strip().lower()
    color, bg, label = METHOD_STYLE.get(
        key, (PALETTE["neutral"], PALETTE["neutral_soft"], (approach or "Unknown").title())
    )
    return f'<span class="badge" style="color:{color};background:{bg};">{label}</span>'


def render_metric_grid(items: list[dict]) -> None:
    card_parts = []
    for item in items:
        sub_html = f'<div class="metric-sub">{item["sub"]}</div>' if item.get("sub") else ""
        card_parts.append(
            '<div class="metric-card">'
            f'<div class="metric-label">{item["label"]}</div>'
            f'<div class="metric-value">{item["value"]}</div>'
            f"{sub_html}"
            "</div>"
        )
    st.markdown(f'<div class="metric-grid">{"".join(card_parts)}</div>', unsafe_allow_html=True)


def fmt(value, decimals: int = 3, suffix: str = "") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    try:
        return f"{float(value):.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def fmt_duration(seconds: float | None) -> str:
    if seconds is None or (isinstance(seconds, float) and pd.isna(seconds)):
        return "—"
    seconds = float(seconds)
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes, secs = divmod(int(round(seconds)), 60)
    if minutes < 60:
        return f"{minutes}m {secs:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def altair_bar(data: pd.DataFrame, x: str, y: str, color: str, title: str = "") -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(f"{x}:N", title=None, sort=None),
            y=alt.Y(f"{y}:Q", title=None),
            color=alt.Color(
                f"{color}:N",
                title=None,
                scale=alt.Scale(range=CHART_COLORS),
                legend=alt.Legend(orient="bottom", symbolType="circle"),
            ),
            xOffset=f"{color}:N",
            tooltip=list(data.columns),
        )
        .properties(height=260, title=title)
        .configure_axis(grid=False, domainColor=PALETTE["border"], labelColor=PALETTE["text_muted"])
        .configure_view(strokeWidth=0)
    )


def altair_stacked_bar(data: pd.DataFrame, x: str, y: str, color: str, colors: dict[str, str]) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X(f"{x}:N", title=None, sort=None),
            y=alt.Y(f"{y}:Q", title=None, stack="zero"),
            color=alt.Color(
                f"{color}:N",
                title=None,
                scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())),
                legend=alt.Legend(orient="bottom", symbolType="circle"),
            ),
            tooltip=list(data.columns),
        )
        .properties(height=300)
        .configure_axis(grid=False, domainColor=PALETTE["border"], labelColor=PALETTE["text_muted"])
        .configure_view(strokeWidth=0)
    )


def altair_donut(
    data: pd.DataFrame,
    category: str,
    value: str,
    colors: dict[str, str],
    inner_radius: int = 58,
    outer_radius: int = 95,
    height: int = 230,
    center_text_size: int = 24,
) -> alt.LayerChart:
    total = data[value].sum()

    arc = (
        alt.Chart(data)
        .mark_arc(innerRadius=inner_radius, outerRadius=outer_radius, cornerRadius=3, padAngle=0.01)
        .encode(
            theta=alt.Theta(f"{value}:Q", stack=True),
            color=alt.Color(
                f"{category}:N",
                title=None,
                scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())),
                legend=alt.Legend(orient="right", symbolType="circle"),
            ),
            tooltip=[category, value],
        )
    )

    center_text = (
        alt.Chart(pd.DataFrame({"text": [f"{total:.0f}"]}))
        .mark_text(size=center_text_size, fontWeight="bold", color=PALETTE["text"])
        .encode(text="text:N")
    )

    return alt.layer(arc, center_text).properties(height=height)


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
# Data access
# ---------------------------------------------------------------------

METRICS = {
    "learning_time_seconds": "Learning time (s)",
    "total_time_seconds": "End-to-end time (s)",
    "number_of_rounds": "Rounds",
    "number_of_programs": "Programs explored",
    "final_score": "Final score",
}

PERFORMANCE_METRICS = {
    "accuracy": "Accuracy",
    "precision": "Precision",
    "recall": "Recall",
    "f1": "F1-score",
}

GROUP_COLUMNS = ["approach", "dataset", "number_of_clients", "partition_strategy"]


def _confusion_to_prf(tp, fn, tn, fp) -> tuple[float | None, float | None, float | None, float | None]:
    tp, fn, tn, fp = float(tp or 0), float(fn or 0), float(tn or 0), float(fp or 0)
    total = tp + fn + tn + fp
    if total <= 0:
        return None, None, None, None
    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )
    return accuracy, precision, recall, f1


@st.cache_data(ttl=30)
def load_benchmarks_df() -> pd.DataFrame:
    """One row per benchmark — what the Experiments page shows as one
    'experiment' card, even though it may bundle several runs."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id, name, created_at, completed_at,
                approach, dataset, number_of_clients, partition_strategy,
                number_of_runs, status
            FROM benchmarks
            ORDER BY created_at DESC
            """
        ).fetchall()

    df = pd.DataFrame([dict(row) for row in rows])
    if df.empty:
        return df

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["completed_at"] = pd.to_datetime(df["completed_at"], errors="coerce")
    df["duration_seconds"] = (df["completed_at"] - df["created_at"]).dt.total_seconds()
    return df


@st.cache_data(ttl=30)
def load_run_level_df() -> pd.DataFrame:
    """One row per individual run (experiment) with server-side timing
    metrics plus an approach-aware accuracy/precision/recall/F1, computed
    from whichever table actually holds real confusion-matrix counts for
    that approach:

      - centralized: server_results.tp/fn/tn/fp (single-process run, the
        server sees the whole test set itself).
      - consensus:   consensus_results (global test set evaluation of the
        consensus hypothesis).
      - collaboration / coordination: SUM(tp/fn/tn/fp) across every
        client_results row for that run — server_results' own tp/fn/tn/fp
        columns are always 0 for these two approaches (never populated),
        but each client's local confusion matrix is real, so summing
        across clients gives a genuine federated-level confusion matrix.
    """

    with get_connection() as connection:
        exp_rows = connection.execute(
            """
            SELECT
                e.id AS experiment_id,
                e.created_at, e.completed_at, e.status,
                e.approach, e.dataset, e.number_of_clients, e.partition_strategy,
                br.benchmark_id, br.run_number,
                sr.total_time_seconds, sr.startup_time_seconds, sr.learning_time_seconds,
                sr.popper_time_seconds, sr.federation_time_seconds,
                sr.number_of_rounds, sr.number_of_programs, sr.final_score,
                sr.tp AS sr_tp, sr.fn AS sr_fn, sr.tn AS sr_tn, sr.fp AS sr_fp
            FROM experiments AS e
            LEFT JOIN server_results AS sr ON sr.experiment_id = e.id
            LEFT JOIN benchmark_runs AS br ON br.experiment_id = e.id
            """
        ).fetchall()

        client_sum_rows = connection.execute(
            """
            SELECT experiment_id, SUM(tp) AS tp, SUM(fn) AS fn, SUM(tn) AS tn, SUM(fp) AS fp
            FROM client_results
            GROUP BY experiment_id
            """
        ).fetchall()

        consensus_rows = connection.execute(
            """
            SELECT experiment_id, tp, fn, tn, fp, accuracy, precision, recall, f1
            FROM consensus_results
            """
        ).fetchall()

    df = pd.DataFrame([dict(row) for row in exp_rows])
    if df.empty:
        return df

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["completed_at"] = pd.to_datetime(df["completed_at"], errors="coerce")

    client_sums = {row["experiment_id"]: dict(row) for row in client_sum_rows}
    consensus = {row["experiment_id"]: dict(row) for row in consensus_rows}

    accuracy_col, precision_col, recall_col, f1_col = [], [], [], []
    for _, row in df.iterrows():
        approach = row["approach"]
        exp_id = row["experiment_id"]

        if approach == "consensus" and exp_id in consensus:
            c = consensus[exp_id]
            if c.get("accuracy") is not None:
                accuracy_col.append(c["accuracy"])
                precision_col.append(c["precision"])
                recall_col.append(c["recall"])
                f1_col.append(c["f1"])
            else:
                a, p, r, f = _confusion_to_prf(c["tp"], c["fn"], c["tn"], c["fp"])
                accuracy_col.append(a); precision_col.append(p); recall_col.append(r); f1_col.append(f)
        elif approach == "centralized":
            a, p, r, f = _confusion_to_prf(row["sr_tp"], row["sr_fn"], row["sr_tn"], row["sr_fp"])
            accuracy_col.append(a); precision_col.append(p); recall_col.append(r); f1_col.append(f)
        elif exp_id in client_sums:
            c = client_sums[exp_id]
            a, p, r, f = _confusion_to_prf(c["tp"], c["fn"], c["tn"], c["fp"])
            accuracy_col.append(a); precision_col.append(p); recall_col.append(r); f1_col.append(f)
        else:
            accuracy_col.append(None); precision_col.append(None); recall_col.append(None); f1_col.append(None)

    df["accuracy"] = accuracy_col
    df["precision"] = precision_col
    df["recall"] = recall_col
    df["f1"] = f1_col

    return df


@st.cache_data(ttl=30)
def load_all_run_results() -> pd.DataFrame:
    """One row per (benchmark, run) with its server-side timing metrics —
    used by the Compare Approaches tab (needs the benchmark_id/config
    grouping, which the run-level loader above doesn't restrict to)."""

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

    df["popper_core_seconds"] = df["popper_time_seconds"].fillna(0.0)
    df["total_popper_time_seconds"] = df["popper_core_seconds"] + df["client_eval_wall"]
    df["federation_overhead_seconds"] = (
        df["federation_time_seconds"].fillna(0.0) - df["client_eval_wall"]
    ).clip(lower=0.0)

    return df


@st.cache_data(ttl=30)
def load_client_and_consensus(experiment_ids: tuple[int, ...]) -> tuple[pd.DataFrame, pd.DataFrame]:
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


def mean_std_str(values: pd.Series, decimals: int = 2) -> str:
    clean = values.dropna()
    if clean.empty:
        return "—"
    m = clean.mean()
    s = clean.std(ddof=0) if len(clean) > 1 else 0.0
    return f"{m:.{decimals}f} ± {s:.{decimals}f}"


# ---------------------------------------------------------------------
# Page body
# ---------------------------------------------------------------------

inject_style()

st.markdown('<div class="breadcrumb">Home &gt; Analytics</div>', unsafe_allow_html=True)

st.title("Analytics")
st.caption("Explore, compare and analyse the results of your federated ILP experiments.")

benchmarks_df = load_benchmarks_df()
run_df = load_run_level_df()

if benchmarks_df.empty:
    st.info("No benchmark has been recorded yet. Run one from the Experiments page first.")
    st.stop()

tab_overview, tab_approach, tab_compare, tab_scalability = st.tabs(
    ["Overview", "Approach Analysis", "Compare Approaches", "Scalability"]
)

# =======================================================================
# TAB 1 — Overview
# =======================================================================

with tab_overview:
    present_approaches_all = set(benchmarks_df["approach"].dropna().unique().tolist())

    total_experiments = len(benchmarks_df)
    completed_experiments = int((benchmarks_df["status"] == "COMPLETED").sum())
    completed_pct = (completed_experiments / total_experiments * 100) if total_experiments else 0.0
    total_datasets = benchmarks_df["dataset"].nunique()
    total_runs = len(run_df) if not run_df.empty else 0
    total_runtime_hours = (
        run_df["total_time_seconds"].fillna(0.0).sum() / 3600.0 if not run_df.empty else 0.0
    )

    render_metric_grid(
        [
            {"label": "Total experiments", "value": total_experiments},
            {"label": "Completed", "value": f"{completed_experiments} ({completed_pct:.0f}%)"},
            {"label": "Datasets", "value": total_datasets},
            {"label": "Total runs", "value": total_runs},
            {"label": "Total runtime", "value": f"{total_runtime_hours:.1f}h"},
        ]
    )

    st.write("")

    # --- Recent experiments + Experiments by approach ---------------------

    left_col, right_col = st.columns([1.3, 1])

    with left_col:
        with st.container(border=True):
            header_left, header_right = st.columns([4, 1])
            with header_left:
                st.markdown('<div class="section-title">Recent experiments</div>', unsafe_allow_html=True)
            with header_right:
                st.page_link(
                    "app_pages/05_Experiments.py",
                    label="View all →",
                    use_container_width=True,
                )

            recent = benchmarks_df.head(8).copy()
            recent["Approach"] = recent["approach"].map(lambda a: render_method_badge(a))
            recent["Status"] = recent["status"].map(lambda s: render_badge(s))
            recent["Start time"] = recent["created_at"].dt.strftime("%Y-%m-%d %H:%M").fillna("—")
            recent["Finish time"] = recent["completed_at"].dt.strftime("%Y-%m-%d %H:%M")
            recent["Finish time"] = recent["Finish time"].where(recent["completed_at"].notna(), "—")
            recent["Duration"] = recent["duration_seconds"].map(fmt_duration)

            table_rows = []
            for _, row in recent.iterrows():
                table_rows.append(
                    "<tr>"
                    f'<td>{row["id"]}</td>'
                    f'<td>{row["Approach"]}</td>'
                    f'<td>{row["dataset"]}</td>'
                    f'<td>{row["number_of_clients"]}</td>'
                    f'<td>{row["partition_strategy"]}</td>'
                    f'<td>{row["Start time"]}</td>'
                    f'<td>{row["Finish time"]}</td>'
                    f'<td>{row["Duration"]}</td>'
                    f'<td>{row["Status"]}</td>'
                    "</tr>"
                )

            table_html = f"""
            <style>
            .recent-table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
            .recent-table th {{
                text-align: left; font-weight: 600; color: {PALETTE["text_muted"]};
                text-transform: uppercase; letter-spacing: 0.03em; font-size: 0.72rem;
                padding: 6px 8px; border-bottom: 1px solid {PALETTE["border"]};
            }}
            .recent-table td {{
                padding: 7px 8px; border-bottom: 1px solid {PALETTE["border"]}; color: {PALETTE["text"]};
                white-space: nowrap;
            }}
            .recent-table tr:last-child td {{ border-bottom: none; }}
            </style>
            <div style="width:100%; overflow-x:auto;">
            <table class="recent-table">
                <thead><tr>
                    <th>ID</th><th>Approach</th><th>Dataset</th><th>Clients (K)</th>
                    <th>Partition</th><th>Start time</th><th>Finish time</th><th>Duration</th><th>Status</th>
                </tr></thead>
                <tbody>{"".join(table_rows)}</tbody>
            </table>
            </div>
            """
            st.markdown(table_html, unsafe_allow_html=True)

    with right_col:
        with st.container(border=True):
            st.markdown('<div class="section-title">Experiments by approach</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-caption">Number of experiments per dataset, split by approach</div>',
                unsafe_allow_html=True,
            )

            by_approach = (
                benchmarks_df.groupby(["dataset", "approach"]).size().reset_index(name="count")
            )
            approach_colors = {a: METHOD_STYLE.get(a, (PALETTE["neutral"],))[0] for a in present_approaches_all}
            st.altair_chart(
                altair_stacked_bar(by_approach, "dataset", "count", "approach", approach_colors),
                use_container_width=True,
            )

    st.write("")

    # --- Overall performance + Runtime distribution + Partition donut ----

    with st.container(border=True):
        st.markdown(
            '<div class="section-title">Overall performance (all approaches, all datasets)</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-caption">Mean ± standard deviation across every run with a computable '
            'confusion matrix — centralized and consensus runs are evaluated on the global test set, '
            'collaboration/coordination runs are the sum of every client\'s local confusion matrix</div>',
            unsafe_allow_html=True,
        )

        perf_left, perf_right = st.columns([1, 1.3])

        with perf_left:
            render_metric_grid(
                [
                    {"label": label, "value": mean_std_str(run_df[key])}
                    for key, label in PERFORMANCE_METRICS.items()
                ]
                if not run_df.empty
                else [{"label": label, "value": "—"} for label in PERFORMANCE_METRICS.values()]
            )

            st.write("")
            st.markdown('<div class="section-title" style="font-size:0.95rem;">Experiments by partition</div>', unsafe_allow_html=True)
            partition_counts = benchmarks_df["partition_strategy"].value_counts().reset_index()
            partition_counts.columns = ["Partition", "Count"]
            partition_palette = {"iid": PALETTE["primary"], "non_iid": PALETTE["success"]}
            for name in partition_counts["Partition"]:
                partition_palette.setdefault(name, PALETTE["neutral"])
            st.altair_chart(
                altair_donut(
                    partition_counts, "Partition", "Count", partition_palette,
                    inner_radius=42, outer_radius=70, height=170, center_text_size=18,
                ),
                use_container_width=True,
            )

        with perf_right:
            st.markdown('<div class="section-title" style="font-size:0.95rem;">Runtime distribution</div>', unsafe_allow_html=True)
            runtime_values = run_df["total_time_seconds"].dropna()
            runtime_values = runtime_values[runtime_values > 0]
            if runtime_values.empty:
                st.info("No completed runs with a recorded runtime yet.")
            else:
                runtime_chart_df = pd.DataFrame({"total_time_seconds": runtime_values})
                runtime_hist = (
                    alt.Chart(runtime_chart_df)
                    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color=PALETTE["primary"])
                    .encode(
                        x=alt.X(
                            "total_time_seconds:Q",
                            bin=alt.Bin(maxbins=25),
                            scale=alt.Scale(type="log", base=10),
                            title="Runtime (s, log scale)",
                        ),
                        y=alt.Y("count():Q", title="Runs"),
                        tooltip=[alt.Tooltip("count():Q", title="Runs")],
                    )
                    .properties(height=230)
                    .configure_axis(grid=False, domainColor=PALETTE["border"], labelColor=PALETTE["text_muted"])
                    .configure_view(strokeWidth=0)
                )
                st.altair_chart(runtime_hist, use_container_width=True)

    st.write("")

    # --- Performance by dataset and approach ------------------------------

    with st.container(border=True):
        header_left, header_right = st.columns([4, 1.3])
        with header_left:
            st.markdown('<div class="section-title">Performance by dataset and approach</div>', unsafe_allow_html=True)
        with header_right:
            perf_metric_key = st.selectbox(
                "Metric",
                options=list(PERFORMANCE_METRICS.keys()),
                format_func=lambda k: PERFORMANCE_METRICS[k],
                key="overview_perf_metric",
                label_visibility="collapsed",
            )

        if run_df.empty:
            st.info("No runs recorded yet.")
        else:
            perf_by_ds = (
                run_df.dropna(subset=[perf_metric_key])
                .groupby(["dataset", "approach"])[perf_metric_key]
                .mean()
                .reset_index()
            )
            if perf_by_ds.empty:
                st.info(f"No data available yet for {PERFORMANCE_METRICS[perf_metric_key]}.")
            else:
                approach_colors = {a: METHOD_STYLE.get(a, (PALETTE["neutral"],))[0] for a in present_approaches_all}
                chart = (
                    alt.Chart(perf_by_ds)
                    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(
                        x=alt.X("dataset:N", title=None, sort=None),
                        xOffset=alt.XOffset("approach:N"),
                        y=alt.Y(f"{perf_metric_key}:Q", title=PERFORMANCE_METRICS[perf_metric_key]),
                        color=alt.Color(
                            "approach:N", title=None,
                            scale=alt.Scale(domain=list(approach_colors.keys()), range=list(approach_colors.values())),
                            legend=alt.Legend(orient="bottom", symbolType="circle"),
                        ),
                        tooltip=["dataset", "approach", alt.Tooltip(f"{perf_metric_key}:Q", format=".3f")],
                    )
                    .properties(height=300)
                    .configure_axis(grid=False, domainColor=PALETTE["border"], labelColor=PALETTE["text_muted"])
                    .configure_view(strokeWidth=0)
                )
                st.altair_chart(chart, use_container_width=True)


# =======================================================================
# TAB 2 — Approach Analysis
# =======================================================================

with tab_approach:
    working_df_full = load_all_run_results()

    if working_df_full.empty:
        st.info("No benchmark runs recorded yet.")
    else:
        present_approaches = set(working_df_full["approach"].dropna().unique().tolist())

        st.markdown('<div class="section-title">Timing breakdown by approach</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-caption">Pick one approach and see, dataset by dataset, how its total time '
            'splits between client-side evaluation, the server\'s own Popper search, and pure federation overhead</div>',
            unsafe_allow_html=True,
        )

        TIMING_COMPONENTS = {
            "client_eval_wall": "Client evaluation time (slowest client)",
            "popper_core_seconds": "Popper core (Tcentral, server-side)",
            "total_popper_time_seconds": "Total Popper time (core + client eval)",
            "federation_overhead_seconds": "Federation overhead (pure communication)",
        }

        timing_approach_options = [a for a in ALL_APPROACHES if a in present_approaches]
        if not timing_approach_options:
            st.info("No approach with recorded runs yet.")
        else:
            timing_approach = st.selectbox("Approach", options=timing_approach_options, key="timing_breakdown_approach")
            timing_df = working_df_full[working_df_full["approach"] == timing_approach].copy()

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
                                "metric:N", title=None, sort=list(TIMING_COMPONENTS.values()),
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

        # --- Per-benchmark detail ------------------------------------------

        st.markdown('<div class="section-title">Per-benchmark detail</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-caption">One row per benchmark — select a row to see its federated client '
            'breakdown and consensus hypothesis, if any</div>',
            unsafe_allow_html=True,
        )

        benchmark_group_columns = ["benchmark_id", "benchmark_name", *GROUP_COLUMNS]
        benchmark_level = (
            working_df_full.groupby(benchmark_group_columns)[list(METRICS.keys())]
            .agg(["mean", "std", "count"])
        )
        benchmark_level.columns = ["_".join(col) for col in benchmark_level.columns]
        benchmark_level = benchmark_level.reset_index()

        benchmark_display_df = benchmark_level[["benchmark_id", "benchmark_name", *GROUP_COLUMNS]].copy()
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

        selected_rows = []
        if benchmark_selection and "selection" in benchmark_selection:
            selected_rows = benchmark_selection["selection"].get("rows", [])

        if selected_rows:
            picked_benchmark_id = int(benchmark_display_df.iloc[selected_rows[0]]["ID"])
            picked_benchmark_name = benchmark_display_df.iloc[selected_rows[0]]["Name"]
            experiment_ids = tuple(
                int(x)
                for x in working_df_full.loc[working_df_full["benchmark_id"] == picked_benchmark_id, "experiment_id"]
                .dropna().unique().tolist()
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
                                "experiment_id": "Run (experiment)", "client_id": "Client",
                                "dataset_partition": "Partition", "number_of_examples": "Examples",
                                "number_of_positive_examples": "Positive", "number_of_negative_examples": "Negative",
                                "average_eval_wall_seconds": "Avg eval time (s)",
                                "accepted_solution": "Accepted solution", "final_score": "Final score",
                            }
                        )
                        client_display["Accepted solution"] = client_display["Accepted solution"].map({1: "yes", 0: "no"})
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
                                "experiment_id": "Run (experiment)", "learner": "Learner",
                                "number_of_clients": "Clients", "number_of_hypotheses": "Hypotheses proposed",
                                "hypotheses": "Hypotheses", "accuracy": "Accuracy", "precision": "Precision",
                                "recall": "Recall", "f1": "F1",
                            }
                        )
                        st.dataframe(consensus_display.drop(columns=["Hypotheses"]), use_container_width=True, hide_index=True)
                        for _, row in consensus_df.iterrows():
                            with st.expander(f"Hypothesis text — run {row['experiment_id']}"):
                                st.code(row["hypotheses"], language="prolog")
        else:
            st.caption("Select a row above to see its federated client breakdown and consensus hypothesis.")


# =======================================================================
# TAB 3 — Compare Approaches
# =======================================================================

with tab_compare:
    raw_df = load_all_run_results()

    if raw_df.empty:
        st.info("No benchmark has been recorded yet.")
    else:
        with st.container(border=True):
            st.markdown('<div class="section-title">Filters</div>', unsafe_allow_html=True)

            only_completed = st.checkbox(
                "Only completed benchmarks", value=True,
                help="Excludes benchmarks that are still running or failed, so partial results don't skew the averages.",
                key="compare_only_completed",
            )

            cwdf = raw_df.copy()
            if only_completed:
                cwdf = cwdf[cwdf["benchmark_status"] == "COMPLETED"]

            filter_columns = st.columns(4)
            with filter_columns[0]:
                present_approaches = set(cwdf["approach"].dropna().unique().tolist())
                approach_options = ALL_APPROACHES + sorted(present_approaches - set(ALL_APPROACHES))
                selected_approaches = st.multiselect(
                    "Approach", options=approach_options,
                    default=[a for a in approach_options if a in present_approaches],
                    key="compare_approach_filter",
                )
            with filter_columns[1]:
                dataset_options = sorted(cwdf["dataset"].dropna().unique().tolist())
                selected_datasets = st.multiselect("Dataset", options=dataset_options, default=dataset_options, key="compare_dataset_filter")
            with filter_columns[2]:
                k_options = sorted(cwdf["number_of_clients"].dropna().unique().tolist())
                selected_k = st.multiselect("Number of clients (K)", options=k_options, default=k_options, key="compare_k_filter")
            with filter_columns[3]:
                partition_options = sorted(cwdf["partition_strategy"].dropna().unique().tolist())
                selected_partitions = st.multiselect("Partition", options=partition_options, default=partition_options, key="compare_partition_filter")

        cwdf = cwdf[
            cwdf["approach"].isin(selected_approaches)
            & cwdf["dataset"].isin(selected_datasets)
            & cwdf["number_of_clients"].isin(selected_k)
            & cwdf["partition_strategy"].isin(selected_partitions)
        ]

        if cwdf.empty:
            st.warning("No data matches the current filters.")
        else:
            cwdf = cwdf.copy()
            cwdf["config"] = (
                cwdf["approach"] + " · " + cwdf["dataset"]
                + " · K=" + cwdf["number_of_clients"].astype(str)
                + " · " + cwdf["partition_strategy"]
            )

            st.write("")
            render_metric_grid(
                [
                    {"label": "Configurations", "value": cwdf.groupby(GROUP_COLUMNS).ngroups},
                    {"label": "Benchmarks", "value": cwdf["benchmark_id"].nunique()},
                    {"label": "Runs", "value": len(cwdf)},
                ]
            )

            st.divider()
            st.markdown('<div class="section-title">Compare configurations</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-caption">Mean ± standard deviation pooled across every run that matches a configuration — '
                'click a bar to drill down into its individual runs below</div>',
                unsafe_allow_html=True,
            )

            aggregated = cwdf.groupby(GROUP_COLUMNS)[list(METRICS.keys())].agg(["mean", "std", "count"])
            aggregated.columns = ["_".join(col) for col in aggregated.columns]
            aggregated = aggregated.reset_index()
            aggregated["config"] = (
                aggregated["approach"] + " · " + aggregated["dataset"]
                + " · K=" + aggregated["number_of_clients"].astype(str)
                + " · " + aggregated["partition_strategy"]
            )

            metric_key = st.selectbox(
                "Metric to compare", options=list(METRICS.keys()), format_func=lambda key: METRICS[key],
                key="compare_metric_key",
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
                chart_event = st.altair_chart(chart, use_container_width=True, on_select="rerun", key="config_compare_chart")

                if chart_event and "selection" in chart_event:
                    selected_configs = sorted(
                        {point["config"] for point in chart_event["selection"].get("config_select", []) if "config" in point}
                    )

            st.write("")

            if selected_configs:
                drill_df = cwdf[cwdf["config"].isin(selected_configs)].copy()
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

                    drill_display = drill_df[["benchmark_name", "run_number", *METRICS.keys()]].rename(
                        columns={"benchmark_name": "Benchmark", "run_number": "Run", **METRICS}
                    )
                    st.dataframe(drill_display, use_container_width=True, hide_index=True)
            else:
                st.caption("No bar selected — click one above to drill into its individual runs.")

            st.write("")

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


# =======================================================================
# TAB 4 — Scalability
# =======================================================================

with tab_scalability:
    if run_df.empty:
        st.info("No runs recorded yet.")
    else:
        st.markdown('<div class="section-title">Performance and timing as the number of clients grows</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-caption">Mean ± standard deviation across runs, grouped by approach — '
            'shows whether an approach holds up (or slows down / degrades) as K increases</div>',
            unsafe_allow_html=True,
        )

        SCALABILITY_METRICS = {**METRICS, **PERFORMANCE_METRICS}

        scal_col1, scal_col2 = st.columns([1, 3])
        with scal_col1:
            scal_metric_key = st.selectbox(
                "Metric", options=list(SCALABILITY_METRICS.keys()),
                format_func=lambda k: SCALABILITY_METRICS[k], key="scalability_metric",
            )
            scal_dataset_options = ["All datasets"] + sorted(run_df["dataset"].dropna().unique().tolist())
            scal_dataset = st.selectbox("Dataset", options=scal_dataset_options, key="scalability_dataset")

        scal_df = run_df.dropna(subset=[scal_metric_key]).copy()
        if scal_dataset != "All datasets":
            scal_df = scal_df[scal_df["dataset"] == scal_dataset]

        with scal_col2:
            if scal_df.empty:
                st.info(f"No data available yet for {SCALABILITY_METRICS[scal_metric_key]}.")
            else:
                scal_agg = (
                    scal_df.groupby(["number_of_clients", "approach"])[scal_metric_key]
                    .agg(["mean", "std", "count"])
                    .reset_index()
                )
                scal_agg["std"] = scal_agg["std"].fillna(0.0)
                present_approaches_scal = set(scal_agg["approach"].unique().tolist())
                approach_colors = {a: METHOD_STYLE.get(a, (PALETTE["neutral"],))[0] for a in present_approaches_scal}

                line_chart = (
                    alt.Chart(scal_agg)
                    .mark_line(point=True, strokeWidth=2.5)
                    .encode(
                        x=alt.X("number_of_clients:O", title="Number of clients (K)"),
                        y=alt.Y("mean:Q", title=SCALABILITY_METRICS[scal_metric_key]),
                        color=alt.Color(
                            "approach:N", title=None,
                            scale=alt.Scale(domain=list(approach_colors.keys()), range=list(approach_colors.values())),
                            legend=alt.Legend(orient="bottom", symbolType="circle"),
                        ),
                        tooltip=["number_of_clients", "approach", alt.Tooltip("mean:Q", format=".3f"), alt.Tooltip("count:Q", title="n")],
                    )
                    .properties(height=340)
                )
                error_band = (
                    alt.Chart(scal_agg)
                    .mark_errorbar()
                    .encode(
                        x=alt.X("number_of_clients:O", title=None),
                        y=alt.Y("mean:Q", title=SCALABILITY_METRICS[scal_metric_key]),
                        yError="std:Q",
                        color=alt.Color("approach:N", title=None, scale=alt.Scale(domain=list(approach_colors.keys()), range=list(approach_colors.values()))),
                    )
                )
                combined = (
                    (line_chart + error_band)
                    .configure_axis(grid=False, domainColor=PALETTE["border"], labelColor=PALETTE["text_muted"])
                    .configure_view(strokeWidth=0)
                )
                st.altair_chart(combined, use_container_width=True)

        if not scal_df.empty:
            st.write("")
            scal_table = scal_agg.copy()
            scal_table["Value"] = [
                f"{m:.3f} ± {s:.3f} (n={int(n)})" for m, s, n in zip(scal_table["mean"], scal_table["std"], scal_table["count"])
            ]
            scal_table = scal_table[["number_of_clients", "approach", "Value"]].rename(
                columns={"number_of_clients": "K", "approach": "Approach"}
            )
            st.dataframe(scal_table, use_container_width=True, hide_index=True)


st.markdown(
    '<div style="margin-top:auto; padding-top:1.2rem; border-top:1px solid #E2E8F5; color:#5B6472; font-size:0.85rem;">© Yasmine Akaichi · FILP Platform</div>',
    unsafe_allow_html=True,
)

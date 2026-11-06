from __future__ import annotations
import json
import re
import sys
from datetime import datetime
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


from core.benchmark_results import (
    load_benchmark_summary,
    load_consensus_benchmark_summary,
    load_consensus_benchmark_runs,
)
from database.connection import get_connection
from database.schema import initialize_database

initialize_database()  # applies pending column migrations
from core.background_run import BackgroundRun
from core.benchmark import BenchmarkConfig
from core.benchmark_launcher import BenchmarkLauncher
from core.port_utils import find_free_port
from apps.run_monitor import render_run_monitor


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Experiments | FILP",
    page_icon=str(Path(__file__).resolve().parents[2] / "assets" / "filp_favicon.png"),
    layout="wide",
)

if hasattr(st, "logo"):
    try:
        st.logo(str(PROJECT_ROOT / "assets" / "filp_sidebar_logo.png"), size="large")
    except Exception:
        pass




# ---------------------------------------------------------------------
# Visual design system
# ---------------------------------------------------------------------
#
# A soft, low-contrast palette for the content area, and a dark navy
# sidebar to match the FILP dashboard mockup. All colors live here so
# the rest of the page only ever refers to a name, not a hex code.

PALETTE = {
    "bg_card": "#F3F4F6",
    "border": "#E5E7EB",
    "text_muted": "#5B6472",
    "text": "#1F2430",
    "primary": "#1B2A4C",
    "primary_soft": "#F3F4F6",
    "success": "#1B2A4C",
    "success_soft": "#E5E7EB",
    "warning": "#1B2A4C",
    "warning_soft": "#E5E7EB",
    "error": "#1B2A4C",
    "error_soft": "#F3F4F6",
    "neutral": "#8A93A3",
    "neutral_soft": "#F3F4F6",
    # Dark sidebar
    "sidebar_bg": "#0F1B33",
    "sidebar_text": "#E5E7EB",
    "sidebar_text_muted": "#1B2A4C",
    "sidebar_active_bg": "#1B2A4C",
    "sidebar_border": "#22314F",
}

CHART_COLORS = ["#1B2A4C", "#1B2A4C", "#C9CED8", "#C9CED8", "#1B2A4C", "#C9CED8"]

# Status colors (text, background): green = completed, blue = running,
# red = failed, amber = stopped by the user, gray = waiting.
STATUS_COLORS = {
    "success": ("#15803D", "#DCFCE7"),
    "running": ("#1D4ED8", "#DBEAFE"),
    "error": ("#B91C1C", "#FEE2E2"),
    "stopped": ("#B45309", "#FEF3C7"),
    "waiting": ("#6B7280", "#F3F4F6"),
}

STATUS_STYLE = {
    "completed": (*STATUS_COLORS["success"], "✓"),
    "success": (*STATUS_COLORS["success"], "✓"),
    "running": (*STATUS_COLORS["running"], "●"),
    "pending": (*STATUS_COLORS["waiting"], "○"),
    "queued": (*STATUS_COLORS["waiting"], "○"),
    "failed": (*STATUS_COLORS["error"], "✕"),
    "error": (*STATUS_COLORS["error"], "✕"),
    # Stopped by the user with no result to keep (see core/run_control.py)
    "stopped": (*STATUS_COLORS["stopped"], "⏹"),
}

METHOD_STYLE = {
    "consensus": ("#C9CED8", "#F3F4F6", "Consensus"),
    "collaboration": ("#1B2A4C", "#F3F4F6", "Collaboration"),
    "coordination": ("#1B2A4C", "#E5E7EB", "Coordination"),
    "mdl_federation": ("#1B2A4C", "#E5E7EB", "MDL Federation"),
    "centralized": ("#1B2A4C", "#E5E7EB", "Centralized"),
}


def inject_style() -> None:
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-feature-settings: "tnum";
        }}

        /* Light gray page backdrop, with the main content floating as a
           white, rounded, shadowed card — matching the FILP mockup. */
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

        /* Key/value rows, used in the "Run information" style cards */
        .kv-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 7px 0;
            border-bottom: 1px solid {PALETTE["border"]};
            font-size: 0.85rem;
        }}
        .kv-row:last-child {{
            border-bottom: none;
        }}
        .kv-label {{
            color: {PALETTE["text_muted"]};
        }}
        .kv-value {{
            color: {PALETTE["text"]};
            font-weight: 600;
        }}

        /* Softer, rounded cards instead of Streamlit's default hard
           white boxes with a heavy border. */
        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            border-radius: 14px !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 14px !important;
        }}

        /* Metric cards */
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

        /* Badges (status, method, votes) */
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }}

        /* Section headers with a little more breathing room */
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

        /* Config chips row */
        .chip-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 6px 0 14px 0;
        }}
        .chip {{
            background: {PALETTE["neutral_soft"]};
            color: {PALETTE["text"]};
            border-radius: 999px;
            padding: 4px 12px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        .chip-neutral {{ background: {PALETTE["neutral_soft"]}; color: {PALETTE["text"]}; }}
        .chip-primary {{ background: {PALETTE["primary_soft"]}; color: {PALETTE["primary"]}; }}
        .chip b {{
            color: {PALETTE["text_muted"]};
            font-weight: 500;
            margin-right: 4px;
        }}

        /* Table header row (list view) */
        .table-head {{
            font-size: 0.78rem;
            font-weight: 600;
            color: {PALETTE["text_muted"]};
            text-transform: uppercase;
            letter-spacing: 0.03em;
            padding-bottom: 6px;
            border-bottom: 1px solid {PALETTE["border"]};
            margin-bottom: 4px;
        }}
        div[data-testid="stHorizontalBlock"] {{
            align-items: center;
        }}

        code, .stCode {{
            font-size: 0.82rem !important;
        }}

        /* Tabs: force the active tab / underline to our blue, not the
           default Streamlit red theme color. */
        button[data-baseweb="tab"] {{
            color: {PALETTE["text_muted"]} !important;
        }}
        .breadcrumb {{
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 4px;
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
        /* Dark navy sidebar, to match the FILP dashboard mockup     */
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
            height: 64px !important;
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
            color: #E5E7EB !important;
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
    return (
        f'<span class="badge" style="color:{color};background:{bg};">'
        f"{dot} {label}</span>"
    )


def render_method_badge(approach: str | None) -> str:
    key = (approach or "").strip().lower()
    color, bg, label = METHOD_STYLE.get(
        key, (PALETTE["neutral"], PALETTE["neutral_soft"], (approach or "Unknown").title())
    )
    return f'<span class="badge" style="color:{color};background:{bg};">{label}</span>'


def render_vote_badge(is_positive: bool) -> str:
    color = PALETTE["success"] if is_positive else PALETTE["error"]
    bg = PALETTE["success_soft"] if is_positive else PALETTE["error_soft"]
    label = "Positive" if is_positive else "Negative"
    dot = "✓" if is_positive else "✕"
    return (
        f'<span class="badge" style="color:{color};background:{bg};">'
        f"{dot} {label}</span>"
    )


def render_metric_grid(items: list[dict]) -> None:
    """items: list of {label, value, sub (optional)}"""

    card_parts = []

    for item in items:
        sub_html = (
            f'<div class="metric-sub">{item["sub"]}</div>' if item.get("sub") else ""
        )
        card_parts.append(
            '<div class="metric-card">'
            f'<div class="metric-label">{item["label"]}</div>'
            f'<div class="metric-value">{item["value"]}</div>'
            f"{sub_html}"
            "</div>"
        )

    cards = "".join(card_parts)
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def render_chips(pairs: list[tuple[str, str]]) -> None:
    chips = "".join(
        f'<span class="chip"><b>{label}</b>{value}</span>' for label, value in pairs
    )
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)


def render_kv_rows(rows: list[tuple[str, str]]) -> None:
    """rows: list of (label, value_html) — value_html may itself contain a badge."""

    parts = "".join(
        f'<div class="kv-row"><span class="kv-label">{label}</span>'
        f'<span class="kv-value">{value}</span></div>'
        for label, value in rows
    )
    st.markdown(parts, unsafe_allow_html=True)


def fmt(value, decimals: int = 3, suffix: str = "") -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def altair_bar(
    data: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str = "",
) -> alt.Chart:
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


def style_pos_neg(value: object) -> str:
    text = str(value).strip().upper()
    if text == "POS":
        return f"color: {PALETTE['success']}; font-weight: 600;"
    if text == "NEG":
        return f"color: {PALETTE['error']}; font-weight: 600;"
    return ""


# ---------------------------------------------------------------------
# Data access helpers
# ---------------------------------------------------------------------

def load_benchmark_metadata(benchmark_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                name,
                created_at,
                approach,
                dataset,
                number_of_clients,
                partition_strategy,
                number_of_runs,
                base_seed,
                learner,
                rounds,
                timeout,
                status,
                reference_benchmark_id
            FROM benchmarks
            WHERE id = ?
            """,
            (benchmark_id,),
        ).fetchone()

    if row is None:
        raise ValueError(f"Benchmark {benchmark_id} was not found.")

    return dict(row)


def load_benchmark_runs(benchmark_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                br.run_number,
                br.random_seed,
                br.experiment_id,
                e.status,
                sr.total_time_seconds,
                sr.startup_time_seconds,
                sr.learning_time_seconds,
                sr.popper_time_seconds,
                sr.federation_time_seconds,
                sr.number_of_rounds,
                sr.number_of_programs,
                sr.final_score,
                sr.solution,
                sr.solution_found
            FROM benchmark_runs br
            JOIN experiments e
                ON e.id = br.experiment_id
            LEFT JOIN server_results sr
                ON sr.experiment_id = e.id
            WHERE br.benchmark_id = ?
            ORDER BY br.run_number
            """,
            (benchmark_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def delete_benchmark(benchmark_id: int) -> None:
    """Permanently delete a benchmark and everything derived from it.

    `benchmark_runs` cascades on `benchmark_id`, but the underlying
    `experiments` rows (and, via their own ON DELETE CASCADE,
    `server_results` / `client_results` / `hypothesis_log` /
    `consensus_results`) are only linked from benchmark_runs.experiment_id
    — deleting the benchmark alone would leave those orphaned. So every
    experiment tied to this benchmark is deleted explicitly first; that
    cascade takes care of the rest, then the (now childless) benchmark
    row itself is removed.
    """
    with get_connection() as connection:
        experiment_ids = [
            row["experiment_id"]
            for row in connection.execute(
                "SELECT experiment_id FROM benchmark_runs WHERE benchmark_id = ?",
                (benchmark_id,),
            ).fetchall()
        ]

        for experiment_id in experiment_ids:
            connection.execute(
                "DELETE FROM experiments WHERE id = ?",
                (experiment_id,),
            )

        connection.execute(
            "DELETE FROM benchmarks WHERE id = ?",
            (benchmark_id,),
        )

        connection.commit()


def load_all_benchmarks(limit: int = 500) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                name,
                created_at,
                approach,
                dataset,
                number_of_clients,
                partition_strategy,
                number_of_runs,
                learner,
                status
            FROM benchmarks
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def load_experiment_durations(benchmark_id: int) -> list[float]:
    """Elapsed seconds per run, computed from experiments.started_at /
    completed_at. Works for every approach, including Consensus, which
    has no dedicated timing table."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT e.started_at, e.completed_at
            FROM benchmark_runs br
            JOIN experiments e ON e.id = br.experiment_id
            WHERE br.benchmark_id = ?
            """,
            (benchmark_id,),
        ).fetchall()

    durations = []
    for row in rows:
        started, completed = row["started_at"], row["completed_at"]
        if not started or not completed:
            continue
        try:
            elapsed = (
                datetime.fromisoformat(completed) - datetime.fromisoformat(started)
            ).total_seconds()
        except ValueError:
            continue
        durations.append(elapsed)

    return durations


def find_benchmark_id_by_experiment(experiment_id: int) -> int | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT benchmark_id
            FROM benchmark_runs
            WHERE experiment_id = ?
            """,
            (experiment_id,),
        ).fetchone()

    if row is None:
        return None

    return int(row["benchmark_id"])


def load_hypothesis_log(experiment_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                sequence_number,
                hypothesis,
                score,
                epsilon_positive,
                epsilon_negative,
                is_final_validation
            FROM hypothesis_log
            WHERE experiment_id = ?
            ORDER BY sequence_number
            """,
            (experiment_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def load_client_results(benchmark_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                br.run_number,
                br.experiment_id,
                cr.client_id,
                cr.dataset_partition,
                cr.number_of_examples,
                cr.number_of_positive_examples,
                cr.number_of_negative_examples,
                cr.number_of_evaluations,
                cr.total_eval_wall_seconds AS total_eval_wall,
                cr.total_eval_cpu_seconds AS total_eval_cpu,
                cr.average_eval_wall_seconds AS average_eval_wall,
                cr.average_eval_cpu_seconds AS average_eval_cpu,
                cr.final_epsilon_positive,
                cr.final_epsilon_negative,
                cr.accepted_solution,
                cr.final_score,
                cr.tp,
                cr.fn,
                cr.tn,
                cr.fp,
                cr.clause_coverage
            FROM benchmark_runs AS br
            JOIN client_results AS cr
                ON cr.experiment_id = br.experiment_id
            WHERE br.benchmark_id = ?
            ORDER BY br.run_number, cr.client_id
            """,
            (benchmark_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def read_text_file(path: str | Path) -> str:
    file_path = Path(path)

    if not file_path.is_file():
        return ""

    return file_path.read_text(encoding="utf-8", errors="replace")


def load_partition_content(partition_path: str) -> dict:
    partition_directory = Path(partition_path)

    return {
        "examples": read_text_file(partition_directory / "exs.pl"),
        "background_knowledge": read_text_file(partition_directory / "bk.pl"),
        "bias": read_text_file(partition_directory / "bias.pl"),
    }


def split_examples(examples_text: str) -> tuple[list[str], list[str]]:
    positive_examples = []
    negative_examples = []

    for line in examples_text.splitlines():
        stripped = line.strip()

        if not stripped or stripped.startswith("%"):
            continue

        if stripped.startswith("pos("):
            positive_examples.append(stripped)
        elif stripped.startswith("neg("):
            negative_examples.append(stripped)

    return positive_examples, negative_examples


# ---------------------------------------------------------------------
# Page body
# ---------------------------------------------------------------------

inject_style()

st.markdown('<div class="breadcrumb">Home &gt; Experiments</div>', unsafe_allow_html=True)

# --- routing between the list view and the detail view --------------------

if "experiments_view" not in st.session_state:
    st.session_state["experiments_view"] = (
        "detail" if st.session_state.get("selected_benchmark_id") else "list"
    )

if st.session_state.get("selected_experiment_id") is not None:
    _benchmark_from_experiment = find_benchmark_id_by_experiment(
        st.session_state["selected_experiment_id"]
    )
    if _benchmark_from_experiment is not None:
        st.session_state["selected_benchmark_id"] = _benchmark_from_experiment
        st.session_state["experiments_view"] = "detail"
    st.session_state.pop("selected_experiment_id", None)

all_benchmarks = load_all_benchmarks()

if not all_benchmarks:
    st.title("Experiments")
    st.caption("Manage and explore your experiments")
    st.info("No experiment has been recorded yet.")
    st.page_link(
        "app_pages/04_Simulation.py",
        label="＋ Simulation",
        use_container_width=False,
    )
    st.stop()

if (
    st.session_state["experiments_view"] != "detail"
    or not st.session_state.get("selected_benchmark_id")
):
    # =======================================================================
    # LIST VIEW
    # =======================================================================

    header_left, header_right = st.columns([4, 1])

    with header_left:
        st.title("Experiments")
        st.caption("Manage and explore your experiments")

    with header_right:
        st.write("")
        if st.button("＋ Simulation", type="primary", use_container_width=True):
            st.switch_page("app_pages/04_Simulation.py")

    st.write("")

    filter_search, filter_method, filter_dataset, filter_status = st.columns([2.2, 1, 1, 1])

    with filter_search:
        search_query = st.text_input(
            "Search",
            placeholder="🔎  Search experiments…",
            label_visibility="collapsed",
        )

    with filter_method:
        method_filter = st.selectbox(
            "Method",
            options=["All methods", "Consensus", "Centralized", "Collaboration", "Coordination", "MDL Federation"],
            label_visibility="collapsed",
        )

    dataset_choices = ["All datasets"] + sorted({b["dataset"] for b in all_benchmarks})

    with filter_dataset:
        dataset_filter = st.selectbox(
            "Dataset", options=dataset_choices, label_visibility="collapsed"
        )

    with filter_status:
        status_filter = st.selectbox(
            "Status",
            options=["All statuses", "Completed", "Running", "Failed", "Stopped"],
            label_visibility="collapsed",
        )

    # New experiments appear on page 1: go back to it when the list has grown,
    # instead of staying on a later page opened before the launch.
    if st.session_state.get("_experiments_seen_total") != len(all_benchmarks):
        st.session_state["experiments_page"] = 1
        st.session_state["_experiments_seen_total"] = len(all_benchmarks)

    filtered_benchmarks = [
        b
        for b in all_benchmarks
        if (
            not search_query
            or search_query.lower() in b["name"].lower()
            or search_query.lower() in b["dataset"].lower()
        )
        and (
            method_filter == "All methods"
            or b["approach"] == method_filter.lower().replace(" ", "_")
        )
        and (dataset_filter == "All datasets" or b["dataset"] == dataset_filter)
        and (
            status_filter == "All statuses"
            or (b["status"] or "").lower() == status_filter.lower()
        )
    ]

    st.write("")

    PAGE_SIZE = 8
    total_pages = max(1, -(-len(filtered_benchmarks) // PAGE_SIZE))

    current_page = st.session_state.get("experiments_page", 1)
    current_page = min(max(current_page, 1), total_pages)

    start_index = (current_page - 1) * PAGE_SIZE
    page_rows = filtered_benchmarks[start_index : start_index + PAGE_SIZE]

    pending_delete_id = st.session_state.get("pending_delete_benchmark_id")

    if pending_delete_id is not None:
        pending_delete_benchmark = next(
            (b for b in all_benchmarks if b["id"] == pending_delete_id),
            None,
        )
        with st.container(border=True):
            st.warning(
                f"Delete experiment #{pending_delete_id}"
                f" ({pending_delete_benchmark['name'] if pending_delete_benchmark else 'unknown'})"
                " and every run, hypothesis and client result under it? "
                "This cannot be undone."
            )
            # Nesting the two buttons inside their own narrow outer
            # column (instead of two wide columns side by side in the
            # full-width row) keeps them right next to each other —
            # with wide columns, the gap between "Delete permanently"
            # and "Cancel" is however much blank space is left in the
            # first (wide) column after the button, not a fixed gap.
            buttons_area, _spacer = st.columns([2, 8])
            confirm_col, cancel_col = buttons_area.columns(2)
            with confirm_col:
                if st.button(
                    "Delete",
                    type="primary",
                    key="confirm_delete_benchmark",
                    use_container_width=True,
                ):
                    delete_benchmark(pending_delete_id)
                    st.session_state.pop("pending_delete_benchmark_id", None)
                    st.success(f"Experiment #{pending_delete_id} deleted.")
                    st.rerun()
            with cancel_col:
                if st.button("Cancel", key="cancel_delete_benchmark", use_container_width=True):
                    st.session_state.pop("pending_delete_benchmark_id", None)
                    st.rerun()
        st.write("")

    if not page_rows:
        st.info("No experiment matches your filters.")
    else:
        COLUMN_WIDTHS = [0.6, 1.4, 1.1, 1.0, 0.6, 1.0, 1.0, 0.6, 0.5]

        head_columns = st.columns(COLUMN_WIDTHS)
        for head_column, label in zip(
            head_columns,
            ["ID", "Name", "Method", "Dataset", "Clients", "Status", "Date", "", ""],
        ):
            with head_column:
                st.markdown(f'<div class="table-head">{label}</div>', unsafe_allow_html=True)

        for benchmark in page_rows:
            row_columns = st.columns(COLUMN_WIDTHS)

            with row_columns[0]:
                st.markdown(f"**#{benchmark['id']}**")
            with row_columns[1]:
                display_name = benchmark.get("name") or "—"
                # Consensus runs: show which local learner was used
                # (e.g. zendo1_consensus_k3_iid -> zendo1_consensus_andante_k3_iid).
                if benchmark.get("approach") == "consensus":
                    learner_label = str(benchmark.get("learner") or "popper").lower()
                    if learner_label not in display_name.lower():
                        if "_consensus_" in display_name:
                            display_name = display_name.replace(
                                "_consensus_",
                                f"_consensus_{learner_label}_",
                                1,
                            )
                        else:
                            display_name = f"{display_name} ({learner_label})"
                st.write(display_name)
            with row_columns[2]:
                st.markdown(render_method_badge(benchmark["approach"]), unsafe_allow_html=True)
            with row_columns[3]:
                st.write(benchmark["dataset"])
            with row_columns[4]:
                st.write(str(benchmark["number_of_clients"]))
            with row_columns[5]:
                st.markdown(render_badge(benchmark["status"]), unsafe_allow_html=True)
            with row_columns[6]:
                st.write((benchmark["created_at"] or "—")[:10])
            with row_columns[7]:
                if st.button("View →", key=f"view_{benchmark['id']}", use_container_width=True):
                    st.session_state["selected_benchmark_id"] = benchmark["id"]
                    st.session_state["experiments_view"] = "detail"
                    st.rerun()
            with row_columns[8]:
                if st.button(
                    "🗑",
                    key=f"delete_{benchmark['id']}",
                    help="Delete this experiment",
                    use_container_width=True,
                ):
                    st.session_state["pending_delete_benchmark_id"] = benchmark["id"]
                    st.rerun()

        st.markdown(
            f'<div style="margin-top:-1.4rem; font-size:0.85rem; '
            f'color:{PALETTE["text_muted"]};">'
            f"Showing {len(page_rows)} of {len(filtered_benchmarks)} experiments</div>",
            unsafe_allow_html=True,
        )

        if total_pages > 1:
            # Compact, frameless page numbers: first, last and a window around
            # the current page ("…" for the gaps), so numbers never stack.
            shown = sorted(
                {1, total_pages}
                | set(range(max(1, current_page - 2), min(total_pages, current_page + 2) + 1))
            )
            items: list = []
            for number in shown:
                if items and number - items[-1] > 1:
                    items.append("…")
                items.append(number)

            # Every item is the same kind of button, so they line up; the
            # current page is highlighted with CSS on its widget key.
            st.markdown(
                f"""
                <style>
                div[data-testid="stHorizontalBlock"]:has(.st-key-page_prev) {{
                    margin-top: -1.6rem;
                }}
                .st-key-page_{current_page} button {{
                    background: {PALETTE["text"]} !important;
                    border-radius: 8px !important;
                }}
                .st-key-page_{current_page} button p {{
                    color: #FFFFFF !important;
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )

            pagination_columns = st.columns(
                [1] * (len(items) + 2) + [12], gap="small"
            )

            with pagination_columns[0]:
                if st.button("‹", disabled=(current_page <= 1), key="page_prev", type="tertiary"):
                    st.session_state["experiments_page"] = current_page - 1
                    st.rerun()

            for offset, item in enumerate(items, start=1):
                with pagination_columns[offset]:
                    if item == "…":
                        st.button("…", disabled=True, key=f"page_gap_{offset}", type="tertiary")
                    elif st.button(str(item), key=f"page_{item}", type="tertiary"):
                        st.session_state["experiments_page"] = item
                        st.rerun()

            with pagination_columns[len(items) + 1]:
                if st.button("›", disabled=(current_page >= total_pages), key="page_next", type="tertiary"):
                    st.session_state["experiments_page"] = current_page + 1
                    st.rerun()

    st.stop()


# =======================================================================
# DETAIL VIEW
# =======================================================================

def render_centralized_baseline_block(consensus: dict) -> None:
    """Launch (or show) the centralized run on the SAME data as a consensus
    experiment, recorded as its own experiment with method "centralized"."""
    with get_connection() as connection:
        baselines = [
            dict(row)
            for row in connection.execute(
                "SELECT id, status FROM benchmarks WHERE reference_benchmark_id = ? "
                "ORDER BY id DESC",
                (consensus["id"],),
            ).fetchall()
        ]

    bg = st.session_state.get(f"_baseline_bg_{consensus['id']}")

    with st.container(border=True):
        st.markdown(
            '<div class="section-title">Centralized baseline on the same data</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-caption">'
            "Runs the same learner once on the whole training set (no clients, no "
            "federation) and scores it on this experiment's test set, for each of "
            f"its {consensus['number_of_runs']} run(s) and seeds. It is saved as its own "
            "experiment, method “centralized”, linked to this one."
            "</div>",
            unsafe_allow_html=True,
        )

        if bg is not None and not bg.done:
            render_run_monitor(
                bg,
                key=f"baseline_{consensus['id']}",
                title="Running the centralized baseline…",
            )
            st.stop()

        if bg is not None and bg.done:
            st.session_state.pop(f"_baseline_bg_{consensus['id']}", None)
            if bg.error is not None:
                st.error(f"The centralized run failed: {bg.error}")
            elif bg.stopped_without_result:
                st.warning("The centralized run was stopped before any result.")
            else:
                st.success(f"Centralized baseline saved as experiment #{bg.result}.")
            baselines = [{"id": bg.result, "status": "COMPLETED"}] + [
                b for b in baselines if b["id"] != bg.result
            ] if bg.result else baselines

        for baseline in baselines:
            columns = st.columns([4, 1])
            columns[0].markdown(
                f"Experiment #{baseline['id']} · {render_badge(baseline['status'])}",
                unsafe_allow_html=True,
            )
            if columns[1].button("Open", key=f"open_baseline_{baseline['id']}"):
                st.session_state["selected_benchmark_id"] = baseline["id"]
                st.session_state["experiments_view"] = "detail"
                st.rerun()

        label = (
            "Run it again"
            if baselines
            else "Run centralized on the same data"
        )
        if st.button(label, key=f"run_baseline_{consensus['id']}", type="primary"):
            config = BenchmarkConfig(
                name=f"Centralized baseline of #{consensus['id']} · {consensus['name']}",
                approach="centralized",
                dataset=consensus["dataset"],
                number_of_clients=1,
                partition_strategy="iid",
                number_of_runs=int(consensus["number_of_runs"]),
                base_seed=int(consensus["base_seed"]),
                learner=consensus.get("learner") or "popper",
                rounds=int(consensus.get("rounds") or 35000),
                timeout=int(consensus.get("timeout") or 600),
                server_address=f"localhost:{find_free_port()}",
                reference_benchmark_id=int(consensus["id"]),
            )
            st.session_state[f"_baseline_bg_{consensus['id']}"] = BackgroundRun(
                lambda control, _config=config: BenchmarkLauncher().run(
                    _config, control=control
                )
            )
            st.rerun()


def render_whole_dataset_baseline_block(benchmark: dict) -> None:
    """Coordination / Collaboration: launch Popper centralized on the WHOLE
    dataset (no train/test split), the fair comparison since these approaches
    also learn from all the examples. Same dataset, seed and number of runs."""
    with get_connection() as connection:
        baselines = [
            dict(row)
            for row in connection.execute(
                "SELECT id, status, number_of_runs FROM benchmarks "
                "WHERE approach = 'centralized' AND dataset = ? "
                "AND reference_benchmark_id IS NULL ORDER BY id DESC",
                (benchmark["dataset"],),
            ).fetchall()
        ]

    key = f"_whole_baseline_bg_{benchmark['id']}"
    bg = st.session_state.get(key)

    with st.container(border=True):
        st.markdown(
            '<div class="section-title">Centralized baseline on the whole dataset</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-caption">'
            "Runs Popper once on all the examples of "
            f"“{benchmark['dataset']}” (no clients, no train/test split), "
            f"{benchmark['number_of_runs']} time(s) with the same seed as this "
            "experiment. Coordination and Collaboration also learn from all the "
            "examples, so this is the fair reference for time and size of the "
            "hypothesis. It is shown in the Coordination tab of Analytics."
            "</div>",
            unsafe_allow_html=True,
        )

        if bg is not None and not bg.done:
            render_run_monitor(
                bg,
                key=f"whole_baseline_{benchmark['id']}",
                title="Running the centralized baseline…",
            )
            st.stop()

        if bg is not None and bg.done:
            st.session_state.pop(key, None)
            if bg.error is not None:
                st.error(f"The centralized run failed: {bg.error}")
            elif bg.stopped_without_result:
                st.warning("The centralized run was stopped before any result.")
            else:
                st.success(f"Centralized baseline saved as experiment #{bg.result}.")
                baselines = [
                    {"id": bg.result, "status": "COMPLETED", "number_of_runs": benchmark["number_of_runs"]}
                ] + [b for b in baselines if b["id"] != bg.result]

        for baseline in baselines:
            columns = st.columns([4, 1])
            columns[0].markdown(
                f"Experiment #{baseline['id']} · {baseline['number_of_runs']} run(s) · "
                f"{render_badge(baseline['status'])}",
                unsafe_allow_html=True,
            )
            if columns[1].button("Open", key=f"open_whole_baseline_{benchmark['id']}_{baseline['id']}"):
                st.session_state["selected_benchmark_id"] = baseline["id"]
                st.session_state["experiments_view"] = "detail"
                st.rerun()

        label = "Run it again" if baselines else "Run centralized on the whole dataset"
        if st.button(label, key=f"run_whole_baseline_{benchmark['id']}", type="primary"):
            config = BenchmarkConfig(
                name=f"Centralized, whole {benchmark['dataset']} · same seed as #{benchmark['id']}",
                approach="centralized",
                dataset=benchmark["dataset"],
                number_of_clients=1,
                partition_strategy="iid",
                number_of_runs=int(benchmark["number_of_runs"]),
                base_seed=int(benchmark["base_seed"]),
                learner="popper",
                rounds=int(benchmark.get("rounds") or 35000),
                timeout=int(benchmark.get("timeout") or 600),
                server_address=f"localhost:{find_free_port()}",
            )
            st.session_state[key] = BackgroundRun(
                lambda control, _config=config: BenchmarkLauncher().run(
                    _config, control=control
                )
            )
            st.rerun()


selected_benchmark_id = st.session_state["selected_benchmark_id"]

metadata = load_benchmark_metadata(selected_benchmark_id)

if metadata["approach"] == "consensus":
    summary = load_consensus_benchmark_summary(selected_benchmark_id)
    runs = load_consensus_benchmark_runs(selected_benchmark_id)
else:
    summary = load_benchmark_summary(selected_benchmark_id)
    runs = load_benchmark_runs(selected_benchmark_id)

# Populated for every approach: Consensus clients only report their local
# dataset partition (used by the Dataset explorer tab below), while
# Collaboration / Coordination clients also report federated evaluation
# metrics (used by the Clients tab).
client_results = load_client_results(selected_benchmark_id)


header_left, header_right = st.columns([5, 1])

with header_left:
    approach_label = METHOD_STYLE.get(
        metadata["approach"], (None, None, metadata["approach"].title())
    )[2]

    if st.button("← Experiments", key="back_to_list", type="tertiary"):
        st.session_state["experiments_view"] = "list"
        st.rerun()

    # Hybrid evaluation (Coordination): second search, tested by ONE client
    # holding the whole dataset ("client 0, centralized").
    is_client_zero = metadata["approach"] in ("coordination", "collaboration") and str(
        metadata.get("name") or ""
    ).startswith("Centralized testing")
    _federated_match = re.search(r"same seed as #(\d+)", str(metadata.get("name") or ""))
    federated_of = int(_federated_match.group(1)) if _federated_match else None

    page_title = (
        f"Centralized baseline of experiment #{metadata['reference_benchmark_id']}"
        if metadata["approach"] == "centralized" and metadata.get("reference_benchmark_id")
        else (
            "Client 0 (centralized) of the hybrid evaluation"
            + (f" — experiment #{federated_of}" if federated_of else "")
            if is_client_zero
            else f"Learning by {approach_label}"
        )
    )
    st.markdown(
        f'<div style="font-size:2rem; font-weight:750; color:{PALETTE["text"]}; '
        f'line-height:1.25;">{page_title}</div>'
        f'<div style="font-size:1.1rem; font-weight:600; color:{PALETTE["text_muted"]}; '
        f'margin:4px 0 2px 0;">'
        f'Experiment #{metadata["id"]}'
        f'<span style="margin-left:10px;">{render_badge(metadata["status"])}</span>'
        f"</div>"
        f'<div style="font-size:1.35rem; font-weight:600; color:{PALETTE["text_muted"]}; '
        f'line-height:1.3; margin-bottom:8px;">{metadata["name"]}</div>',
        unsafe_allow_html=True,
    )

    header_chips = [
        (metadata["dataset"].title(), ""),
        ("Clients", str(metadata["number_of_clients"])),
        ("Partition", (metadata["partition_strategy"] or "").upper()),
        ("Runs", str(metadata["number_of_runs"])),
        ("Seed", str(metadata["base_seed"])),
    ]
    if metadata["approach"] == "consensus":
        header_chips.append(("Learner", str(metadata.get("learner") or "popper").title()))
    header_chips.append(("Date", (metadata.get("created_at") or "—")[:10]))
    render_chips(header_chips)

    if is_client_zero:
        st.info(
            "**Client 0 (centralized)** is the second search of the hybrid evaluation "
            "(Bach4Popper, centralized testing). It is the same search as "
            + (f"experiment #{federated_of}" if federated_of else "the federated one")
            + ", but a single client that holds the WHOLE dataset tests every program, and "
            "its outcome gives the constraints directly (no aggregation over several clients). "
            "Its times (learning, Popper core, client evaluation) are compared with the "
            "federated search in Analytics."
        )

with header_right:
    st.write("")
    download_df = pd.DataFrame(runs)
    st.download_button(
        "⬇ Download results",
        data=download_df.to_csv(index=False).encode("utf-8"),
        file_name=f"experiment_{metadata['id']}_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    if st.button("🗑 Delete experiment", key="delete_from_detail", use_container_width=True):
        st.session_state["pending_delete_benchmark_id"] = metadata["id"]
        st.rerun()

if st.session_state.get("pending_delete_benchmark_id") == metadata["id"]:
    with st.container(border=True):
        st.warning(
            f"Delete experiment #{metadata['id']} ({metadata['name']}) and "
            "every run, hypothesis and client result under it? This cannot "
            "be undone."
        )
        buttons_area, _spacer = st.columns([2, 8])
        confirm_col, cancel_col = buttons_area.columns(2)
        with confirm_col:
            if st.button(
                "Delete",
                type="primary",
                key="confirm_delete_from_detail",
                use_container_width=True,
            ):
                delete_benchmark(metadata["id"])
                st.session_state.pop("pending_delete_benchmark_id", None)
                st.session_state.pop("selected_benchmark_id", None)
                st.session_state["experiments_view"] = "list"
                st.success(f"Experiment #{metadata['id']} deleted.")
                st.rerun()
        with cancel_col:
            if st.button("Cancel", key="cancel_delete_from_detail", use_container_width=True):
                st.session_state.pop("pending_delete_benchmark_id", None)
                st.rerun()

st.write("")

is_consensus_approach = metadata["approach"] == "consensus"

if is_consensus_approach:
    tab_overview, tab_models, tab_predictions, tab_clients, tab_dataset = st.tabs(
        ["Overview", "Models", "Predictions", "Clients", "🔍 Dataset"]
    )
elif metadata["approach"] in ("coordination", "collaboration"):
    # Coordination / Collaboration: extra tab comparing the tested programs of the federated
    # search with those of "Client 0 (centralized)" (hybrid evaluation).
    tab_overview, tab_models, tab_clients, tab_hypotheses, tab_dataset = st.tabs(
        ["Overview", "Models", "Clients", "Hypotheses", "🔍 Dataset"]
    )
    tab_predictions = None
else:
    tab_overview, tab_models, tab_clients, tab_dataset = st.tabs(
        ["Overview", "Models", "Clients", "🔍 Dataset"]
    )
    tab_predictions = None
    tab_hypotheses = None

# --- Overview tab ------------------------------------------------------

with tab_overview:
    if metadata["approach"] == "centralized" and metadata.get("reference_benchmark_id"):
        with st.container(border=True):
            st.markdown(
                "This run is the **centralized baseline** of consensus experiment "
                f"#{metadata['reference_benchmark_id']}: the same learner, run once on the "
                "whole training set, scored on the same test set (same dataset and seeds)."
            )
            if st.button(
                f"Open consensus experiment #{metadata['reference_benchmark_id']}",
                key="open_reference_consensus",
            ):
                st.session_state["selected_benchmark_id"] = metadata["reference_benchmark_id"]
                st.session_state["experiments_view"] = "detail"
                st.rerun()

    if metadata["approach"] == "consensus":
        render_centralized_baseline_block(metadata)

    if metadata["approach"] in ("coordination", "collaboration"):
        render_whole_dataset_baseline_block(metadata)

    if metadata["approach"] == "consensus":
        with st.container(border=True):
            st.markdown(
                '<div class="section-title">Consensus performance</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="section-caption">'
                "Global majority-vote performance on the shared test set"
                "</div>",
                unsafe_allow_html=True,
            )

            render_metric_grid(
                [
                    {"label": "Accuracy", "value": fmt(summary.accuracy.mean), "sub": f"± {fmt(summary.accuracy.std)}"},
                    {"label": "Precision", "value": fmt(summary.precision.mean), "sub": f"± {fmt(summary.precision.std)}"},
                    {"label": "Recall", "value": fmt(summary.recall.mean), "sub": f"± {fmt(summary.recall.std)}"},
                    {"label": "F1 score", "value": fmt(summary.f1.mean), "sub": f"± {fmt(summary.f1.std)}"},
                ]
            )

            with st.expander("ℹ️ What do these metrics mean?"):
                st.markdown(
                    "All four are computed on the shared **test set**, from the "
                    "confusion matrix TP / TN / FP / FN (visible below in "
                    "*Prediction distribution*):\n\n"
                    "- **Accuracy** — share of *all* test examples the consensus "
                    "got right: `(TP + TN) / (TP + TN + FP + FN)`.\n"
                    "- **Precision** — of the examples the consensus predicted "
                    "**positive**, how many actually were: `TP / (TP + FP)`. "
                    "Low precision means false alarms.\n"
                    "- **Recall** — of the examples that were *actually* "
                    "positive, how many the consensus found: `TP / (TP + FN)`. "
                    "Low recall means missed positives.\n"
                    "- **F1 score** — the harmonic mean of precision and "
                    "recall, a single number that penalizes both false "
                    "alarms and missed positives.\n\n"
                    "When every client's hypothesis covers the test set "
                    "perfectly (FP = FN = 0, as in most small benchmarks "
                    "here), all four collapse to **1.00** — that's expected, "
                    "not a bug."
                )

        # Each hypothesis alone vs. the majority vote, on the same shared
        # test set (from consensus_analysis.json, averaged over the runs).
        per_hypothesis_rows: dict[str, list[dict]] = {}
        analysis_runs = 0
        for run in runs or []:
            analysis_file = (
                PROJECT_ROOT
                / "artifacts"
                / f"experiment_{run['experiment_id']}"
                / "consensus"
                / "consensus_analysis.json"
            )
            if not analysis_file.is_file():
                continue
            try:
                analysis = json.loads(analysis_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not analysis.get("consensus"):
                continue
            analysis_runs += 1
            per_hypothesis_rows.setdefault("Consensus (majority vote)", []).append(analysis["consensus"])
            for name, values in analysis.get("per_hypothesis", {}).items():
                per_hypothesis_rows.setdefault(f"{name} alone", []).append(values)

        if per_hypothesis_rows:
            with st.container(border=True):
                st.markdown(
                    '<div class="section-title">Each hypothesis alone vs. the consensus</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="section-caption">'
                    "Every hypothesis H1, H2, ... evaluated alone on the same "
                    "shared test set, next to the majority vote"
                    + (f" (mean over {analysis_runs} runs)" if analysis_runs > 1 else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )

                def _mean(items: list[dict], key: str) -> float:
                    return sum(item[key] for item in items) / len(items)

                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Model": label,
                                "Accuracy": _mean(items, "accuracy"),
                                "Precision": _mean(items, "precision"),
                                "Recall": _mean(items, "recall"),
                                "F1": _mean(items, "f1"),
                                "MCC": _mean(items, "mcc"),
                            }
                            for label, items in per_hypothesis_rows.items()
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        name: st.column_config.NumberColumn(format="%.3f")
                        for name in ("Accuracy", "Precision", "Recall", "F1", "MCC")
                    },
                )
                st.caption(
                    "The accuracy shown at the top is the first row: the "
                    "result of the vote, not of one particular hypothesis or "
                    "client. MCC (−1 to +1) stays reliable when positives and "
                    "negatives are unbalanced."
                )

        # Cost of the run: learning time of every client and the size of the
        # messages (from consensus_analysis.json, averaged over the runs).
        slowest_times: list[float] = []
        mean_times: list[float] = []
        upload_totals: list[float] = []
        ensemble_sizes: list[float] = []
        round_times: list[float] = []
        for run in runs or []:
            cost_file = (
                PROJECT_ROOT
                / "artifacts"
                / f"experiment_{run['experiment_id']}"
                / "consensus"
                / "consensus_analysis.json"
            )
            if not cost_file.is_file():
                continue
            try:
                cost = json.loads(cost_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            times = [
                float(value)
                for value in (cost.get("induction_time_per_client") or {}).values()
            ]
            if times:
                slowest_times.append(max(times))
                mean_times.append(sum(times) / len(times))
            if cost.get("federated_round_seconds") is not None:
                round_times.append(float(cost["federated_round_seconds"]))
            communication = cost.get("communication") or {}
            if communication:
                upload_totals.append(
                    float(sum((communication.get("upload_bytes_per_client") or {}).values()))
                )
                ensemble_sizes.append(float(communication.get("ensemble_bytes", 0.0)))

        if slowest_times:
            with st.container(border=True):
                st.markdown(
                    '<div class="section-title">Cost of the consensus run</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="section-caption">'
                    "Clients learn in parallel, so the learning time of the run "
                    "is the slowest client"
                    + (f" (mean over {len(slowest_times)} runs)" if len(slowest_times) > 1 else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )
                cost_columns = st.columns(5 if round_times else 4)
                if round_times:
                    cost_columns[4].metric(
                        "Total run time",
                        f"{sum(round_times) / len(round_times):.1f} s",
                    )
                cost_columns[0].metric(
                    "Learning time (slowest client)",
                    f"{sum(slowest_times) / len(slowest_times):.1f} s",
                )
                cost_columns[1].metric(
                    "Learning time (mean per client)",
                    f"{sum(mean_times) / len(mean_times):.1f} s",
                )
                cost_columns[2].metric(
                    "Hypotheses sent to the server",
                    f"{sum(upload_totals) / max(len(upload_totals), 1) / 1024:.1f} KB",
                )
                cost_columns[3].metric(
                    "Ensemble sent back to each client",
                    f"{sum(ensemble_sizes) / max(len(ensemble_sizes), 1) / 1024:.1f} KB",
                )

        st.write("")

        overview_left, overview_right, overview_info = st.columns([1, 1.1, 1])

        total_examples = (
            summary.tp.mean + summary.tn.mean + summary.fp.mean + summary.fn.mean
        )
        correct_examples = summary.tp.mean + summary.tn.mean

        # Unanimous vs. disagreement predictions, read from the latest
        # run's vote traces when available (real data, not an average).
        unanimous_count = None
        disagreement_count = None

        if runs:
            latest_experiment_id = runs[-1]["experiment_id"]
            latest_traces_path = (
                PROJECT_ROOT
                / "artifacts"
                / f"experiment_{latest_experiment_id}"
                / "consensus"
                / "vote_traces.json"
            )
            if latest_traces_path.is_file():
                try:
                    latest_traces = json.loads(latest_traces_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    latest_traces = []

                if latest_traces:
                    unanimous_count = sum(
                        1
                        for trace in latest_traces
                        if trace["positive_votes"] in (0, trace["number_of_voters"])
                    )
                    disagreement_count = len(latest_traces) - unanimous_count

        with overview_left:
            with st.container(border=True):
                st.markdown('<div class="section-title">Test set results</div>', unsafe_allow_html=True)
                st.markdown(f"📄 &nbsp; **{fmt(total_examples, 0)}** test examples")
                st.markdown(f"✅ &nbsp; **{fmt(correct_examples, 0)}** correct predictions")
                if unanimous_count is not None:
                    st.markdown(f"🤝 &nbsp; **{unanimous_count}** unanimous predictions")
                    st.markdown(f"⚠️ &nbsp; **{disagreement_count}** with disagreement")
                st.caption(
                    "Averaged across all runs in this benchmark. See the "
                    "Predictions tab for a per-example, per-run breakdown."
                )

        with overview_right:
            with st.container(border=True):
                st.markdown('<div class="section-title">Prediction distribution</div>', unsafe_allow_html=True)
                donut_data = pd.DataFrame(
                    {
                        "Outcome": ["True Positives", "True Negatives", "False Positives", "False Negatives"],
                        "Count": [summary.tp.mean, summary.tn.mean, summary.fp.mean, summary.fn.mean],
                    }
                )
                donut_colors = {
                    "True Positives": PALETTE["primary"],
                    "True Negatives": PALETTE["success"],
                    "False Positives": PALETTE["warning"],
                    "False Negatives": PALETTE["error"],
                }
                st.altair_chart(
                    altair_donut(donut_data, "Outcome", "Count", donut_colors),
                    use_container_width=True,
                )

        durations = load_experiment_durations(selected_benchmark_id)
        total_time_label = (
            f"{fmt(sum(durations) / len(durations))} s" if durations else "—"
        )

        with overview_info:
            with st.container(border=True):
                st.markdown('<div class="section-title">Run information</div>', unsafe_allow_html=True)
                render_kv_rows(
                    [
                        ("Status", render_badge(metadata["status"])),
                        ("Total time", total_time_label),
                        ("Runs", str(summary.number_of_runs)),
                        ("Learner", str(metadata.get("learner") or "popper").title()),
                        ("Hypotheses / run", fmt(summary.number_of_hypotheses.mean, 1)),
                    ]
                )

    else:
        with st.container(border=True):
            st.markdown('<div class="section-title">Timing</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-caption">Mean ± standard deviation across all runs</div>',
                unsafe_allow_html=True,
            )

            render_metric_grid(
                [
                    {"label": "Learning time", "value": f"{fmt(summary.learning_time.mean)} s", "sub": f"± {fmt(summary.learning_time.std)} s"},
                    {"label": "Startup time", "value": f"{fmt(summary.startup_time.mean)} s", "sub": f"± {fmt(summary.startup_time.std)} s"},
                    {"label": "End-to-end time", "value": f"{fmt(summary.total_time.mean)} s", "sub": f"± {fmt(summary.total_time.std)} s"},
                    {"label": "Total Popper time", "value": f"{fmt(summary.popper_time.mean)} s", "sub": f"± {fmt(summary.popper_time.std)} s"},
                    {"label": "Client evaluation time", "value": f"{fmt(summary.client_eval_time.mean)} s", "sub": f"± {fmt(summary.client_eval_time.std)} s"},
                    {"label": "Popper core (server)", "value": f"{fmt(summary.popper_core_time.mean)} s", "sub": f"± {fmt(summary.popper_core_time.std)} s"},
                    {"label": "Federation overhead", "value": f"{fmt(summary.federation_time.mean)} s", "sub": f"± {fmt(summary.federation_time.std)} s"},
                    # "Evaluate-phase test (duplicate)" card removed from
                    # the grid: Flower's second per-round evaluate() phase
                    # is now disabled (fraction_evaluate=0.0 in server.py),
                    # so summary.evaluate_phase_time is always ~0 and the
                    # card had nothing left to show. The underlying field,
                    # DB columns and instrumentation are kept as-is (not
                    # deleted) in case that phase is ever re-enabled —
                    # just re-add this line to bring the card back:
                    # {"label": "Evaluate-phase test (duplicate)", "value": f"{fmt(summary.evaluate_phase_time.mean)} s", "sub": f"± {fmt(summary.evaluate_phase_time.std)} s"},
                ]
            )

            with st.expander("ℹ️ What do these timings mean?"):
                st.markdown(
                    "- **Startup time** — spinning up the federated server and "
                    "connecting all clients before learning starts.\n"
                    "- **Total Popper time** — time spent in Popper's actual "
                    "generate-test-constrain search: **Popper core (server)** "
                    "*plus* **Client evaluation time** below (that client-side "
                    "coverage testing is real Popper work, even though it "
                    "physically runs on the clients).\n"
                    "- **Popper core (server)** — Tcentral: the server's own "
                    "generate/build/ground/constrain steps (proposing the next "
                    "candidate program AND turning its test outcome into new "
                    "ASP constraints), excluding anything done by the "
                    "clients.\n"
                    "- **Client evaluation time** — the slowest client's "
                    "total time testing the proposed programs against its "
                    "local examples (the max across clients, not the sum: "
                    "clients evaluate in parallel, so the server only ever "
                    "waits on whichever one is slowest).\n"
                    "- **Federation overhead** — pure communication/"
                    "aggregation cost: broadcasting hypotheses to clients, "
                    "waiting on the network, aggregating feedback — with the "
                    "clients' own evaluation time excluded. Flower's second, "
                    "separate per-round evaluation phase (`fraction_evaluate`)"
                    " used to re-test every hypothesis a second time here, "
                    "for no functional benefit (nothing in the search reads "
                    "its result) — it's now disabled, which is why this "
                    "number is much smaller than it used to be on "
                    "search-heavy datasets.\n"
                    "- **Learning time** — the full federated loop, measured "
                    "directly end-to-end (from the moment clients are ready "
                    "to the moment a solution is found, a timeout hits, or "
                    "the search is exhausted). Popper core (server) now "
                    "includes the GENERATE step for every round, so Total "
                    "Popper time + Federation overhead should track Learning "
                    "time closely, modulo small aggregation/bookkeeping "
                    "gaps.\n"
                    "- **End-to-end time** — startup + learning + a small "
                    "amount of wrap-up (final aggregation/evaluation), the "
                    "total wall-clock time for the run.\n\n"
                    "Total Popper time already includes the clients' coverage-"
                    "testing time, so it's directly comparable to a "
                    "centralized run's Popper time. See the Analytics page's "
                    "\"Timing breakdown by method\" section for the full "
                    "split (client eval / Tcentral / total Popper / "
                    "federation) across datasets."
                )

        st.write("")

        outcome_left, outcome_right, outcome_info = st.columns([1, 1.1, 1])

        NAVY = "#1B2A4C"

        # Flat, single-color line icons (Canva-style) instead of emoji,
        # so the card matches the rest of the dashboard's design system.
        ICON_ROUNDS = (
            f'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" '
            f'stroke="{NAVY}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M21 12a9 9 0 1 1-2.64-6.36"/><polyline points="21 3 21 9 15 9"/>'
            "</svg>"
        )
        ICON_PROGRAMS = (
            f'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" '
            f'stroke="{NAVY}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<polygon points="12 2 2 7 12 12 22 7 12 2"/>'
            '<polyline points="2 17 12 22 22 17"/>'
            '<polyline points="2 12 12 17 22 12"/>'
            "</svg>"
        )
        ICON_SCORE = (
            f'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" '
            f'stroke="{NAVY}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2" fill="{}"/>'.format(NAVY)
            + "</svg>"
        )

        with outcome_left:
            with st.container(border=True):
                st.markdown('<div class="section-title">Learning outcome</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div style="display:flex; align-items:center; gap:8px; margin:6px 0;">'
                    f'{ICON_ROUNDS}<span><strong>{fmt(summary.number_of_rounds.mean, 1)}</strong> rounds</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="display:flex; align-items:center; gap:8px; margin:6px 0;">'
                    f'{ICON_PROGRAMS}<span><strong>{fmt(summary.number_of_programs.mean, 1)}</strong> programs explored</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="display:flex; align-items:center; gap:8px; margin:6px 0;">'
                    f'{ICON_SCORE}<span><strong>{fmt(summary.final_score.mean, 2)}</strong> final score</span></div>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Averaged across all runs in this benchmark. See the "
                    "Models tab for the hypothesis and per-client contribution."
                )

        latest_run_number = runs[-1]["run_number"] if runs else None
        latest_run_solution_found = bool(runs[-1]["solution_found"]) if runs else False
        latest_client_rows = [
            row
            for row in client_results
            if latest_run_number is not None and int(row["run_number"]) == latest_run_number
        ]
        expected_clients = int(metadata.get("number_of_clients") or 0)
        connected_clients = len(latest_client_rows)

        with outcome_right:
            with st.container(border=True):
                st.markdown('<div class="section-title">Clients connected</div>', unsafe_allow_html=True)
                if expected_clients:
                    not_connected_clients = max(expected_clients - connected_clients, 0)
                    connection_data = pd.DataFrame(
                        {
                            "Status": ["Connected", "Not connected"],
                            "Count": [connected_clients, not_connected_clients],
                        }
                    )
                    connection_colors = {
                        "Connected": PALETTE["success"],
                        "Not connected": PALETTE["error"],
                    }
                    st.altair_chart(
                        altair_donut(
                            connection_data,
                            "Status",
                            "Count",
                            connection_colors,
                            inner_radius=36,
                            outer_radius=60,
                            height=140,
                            center_text_size=16,
                        ),
                        use_container_width=True,
                    )
                    connected_ids = sorted(int(row["client_id"]) for row in latest_client_rows)
                    st.caption(
                        f"Clients {', '.join(str(cid) for cid in connected_ids)} reported a "
                        "result for the latest run."
                        if connected_ids
                        else "No client reported a result for the latest run."
                    )
                else:
                    st.info("No client-level results available for this run.")

        with outcome_info:
            with st.container(border=True):
                st.markdown('<div class="section-title">Run information</div>', unsafe_allow_html=True)
                # Rounds only stopped the search for the centralized
                # approach; Collaboration/Coordination now stop on
                # --timeout instead (search runs until an exact
                # solution or the timeout, whichever comes first — see
                # FedPopper/srvpopper.py), so showing "Max rounds" for
                # those was stale and misleading (rounds is still
                # accepted for backward compatibility but no longer
                # checked as a stop condition).
                if metadata["approach"] in ("collaboration", "coordination", "consensus"):
                    stop_condition_row = (
                        "Timeout",
                        f"{fmt(metadata.get('timeout'), 0)} s" if metadata.get("timeout") else "—",
                    )
                else:
                    stop_condition_row = ("Max rounds", str(metadata.get("rounds") or "—"))

                render_kv_rows(
                    [
                        ("Status", render_badge(metadata["status"])),
                        ("Total time", f"{fmt(summary.total_time.mean)} s"),
                        ("Runs", str(summary.number_of_runs)),
                        stop_condition_row,
                        ("Clients", str(metadata["number_of_clients"])),
                    ]
                )

# --- Models tab ----------------------------------------------------------

with tab_models:
    st.markdown('<div class="section-title">Learned hypotheses</div>', unsafe_allow_html=True)

    if metadata["approach"] == "consensus":
        st.markdown(
            '<div class="section-caption">Local hypotheses learned independently by each client.</div>',
            unsafe_allow_html=True,
        )

        if not runs:
            st.info("No runs available.")
        else:
            if len(runs) > 1:
                model_run_number = st.selectbox(
                    "Run",
                    options=[r["run_number"] for r in runs],
                    format_func=lambda n: f"Run {n}",
                    key="models_run_picker",
                )
                model_row = next(r for r in runs if r["run_number"] == model_run_number)
            else:
                model_row = runs[0]

            hypotheses_raw = model_row.get("hypotheses")
            try:
                hypotheses = json.loads(hypotheses_raw) if hypotheses_raw else []
            except (json.JSONDecodeError, TypeError):
                hypotheses = []

            if not hypotheses:
                st.caption("No saved hypotheses for this experiment.")
            else:
                MAX_COLUMNS_PER_ROW = 4
                indexed_hypotheses = list(enumerate(hypotheses, start=1))
                for row_start in range(0, len(indexed_hypotheses), MAX_COLUMNS_PER_ROW):
                    row_items = indexed_hypotheses[row_start:row_start + MAX_COLUMNS_PER_ROW]
                    model_columns = st.columns(len(row_items))

                    for column, (index, hypothesis) in zip(model_columns, row_items):
                        with column:
                            with st.container(border=True):
                                st.markdown(f"**Client {index} — H{index}**")
                                if hypothesis:
                                    st.code("\n".join(hypothesis), language="prolog")
                                else:
                                    st.caption(
                                        "Empty hypothesis — always votes negative, "
                                        "still counts towards the majority."
                                    )

    else:
        st.markdown(
            '<div class="section-caption">Final program produced by each run, and how each client\'s local evaluation contributed to it.</div>',
            unsafe_allow_html=True,
        )

        for row in runs:
            experiment_id = row["experiment_id"]
            solution = row.get("solution")

            with st.expander(
                f"Run {row['run_number']} · experiment #{experiment_id}",
                expanded=(len(runs) == 1),
            ):
                if not solution:
                    st.caption("No saved hypothesis for this experiment.")
                    continue

                st.code(solution, language="prolog")

                run_client_rows = sorted(
                    (
                        client_row
                        for client_row in client_results
                        if int(client_row["run_number"]) == row["run_number"]
                    ),
                    key=lambda client_row: client_row["client_id"],
                )

                if not run_client_rows:
                    continue

                st.write("")
                st.markdown("**Client contribution to this hypothesis**")

                MAX_COLUMNS_PER_ROW = 4
                for row_start in range(0, len(run_client_rows), MAX_COLUMNS_PER_ROW):
                    row_client_rows = run_client_rows[row_start:row_start + MAX_COLUMNS_PER_ROW]
                    contribution_columns = st.columns(len(row_client_rows))

                    for column, client_row in zip(contribution_columns, row_client_rows):
                        with column:
                            with st.container(border=True):
                                accepted = bool(client_row["accepted_solution"])
                                epsilon_positive = client_row["final_epsilon_positive"] or "—"
                                epsilon_negative = client_row["final_epsilon_negative"] or "—"
                                local_tp = client_row["tp"] or 0
                                local_fp = client_row["fp"] or 0
                                local_positives = client_row["number_of_positive_examples"] or 0
                                local_negatives = client_row["number_of_negative_examples"] or 0
                                st.markdown(f"**Client {client_row['client_id']}**")
                                st.caption(f"ε+ = {epsilon_positive}, ε− = {epsilon_negative}")
                                st.caption(f"Score: {client_row['final_score']}")
                                st.caption(f"Positive covered: {local_tp}/{local_positives}")
                                st.caption(f"Negative covered: {local_fp}/{local_negatives}")
                                st.markdown(
                                    render_badge("completed" if accepted else "pending"),
                                    unsafe_allow_html=True,
                                )

                hypothesis_log_rows = load_hypothesis_log(experiment_id)

                if hypothesis_log_rows:
                    st.write("")
                    st.markdown("**Every hypothesis tested this run**")
                    st.caption(
                        "Sorted by score — confirms the hypothesis above "
                        "really is the best-scoring one, not just the "
                        "last one tried before stopping."
                    )

                    hypothesis_log_df = pd.DataFrame(hypothesis_log_rows)
                    hypothesis_log_df = hypothesis_log_df.sort_values(
                        "score",
                        ascending=False,
                    ).reset_index(drop=True)
                    hypothesis_log_df["role"] = hypothesis_log_df[
                        "is_final_validation"
                    ].map(
                        {1: "Final validation", 0: "Search"}
                    )

                    st.dataframe(
                        hypothesis_log_df[
                            [
                                "sequence_number",
                                "hypothesis",
                                "score",
                                "epsilon_positive",
                                "epsilon_negative",
                                "role",
                            ]
                        ].rename(
                            columns={
                                "sequence_number": "Program",
                                "hypothesis": "Hypothesis",
                                "score": "Score",
                                "epsilon_positive": "ε+",
                                "epsilon_negative": "ε−",
                                "role": "Round type",
                            }
                        ),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Program": st.column_config.NumberColumn(width="small"),
                            # "large" here isn't about making the column
                            # wider than the others by force — it's so
                            # the grid gives it most of the leftover
                            # width instead of Program/Score/ε±/Round
                            # type, which only ever hold a few
                            # characters. A long hypothesis still won't
                            # always fit on one line: click the cell to
                            # open it and scroll/select the full text.
                            "Hypothesis": st.column_config.TextColumn(width="large"),
                            "Score": st.column_config.NumberColumn(width="small"),
                            "ε+": st.column_config.TextColumn(width="small"),
                            "ε−": st.column_config.TextColumn(width="small"),
                            "Round type": st.column_config.TextColumn(width="small"),
                        },
                    )
                    st.caption(
                        "Click a row's Hypothesis cell to expand it and "
                        "see the full program if it doesn't fit on one line."
                    )

# --- Predictions tab (Consensus only — Collaboration / Coordination ------
# --- don't record example-level predictions, so the tab doesn't exist) ---

if tab_predictions is not None:
    with tab_predictions:
        st.markdown('<div class="section-title">Test set predictions</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-caption">View the prediction of each client and the final majority vote.</div>',
            unsafe_allow_html=True,
        )

        if not runs:
            st.info("No Consensus runs available.")
        else:
            if len(runs) > 1:
                prediction_run_number = st.selectbox(
                    "Run",
                    options=[r["run_number"] for r in runs],
                    format_func=lambda n: f"Run {n}",
                    key="predictions_run_picker",
                )
                prediction_row = next(r for r in runs if r["run_number"] == prediction_run_number)
            else:
                prediction_row = runs[0]

            experiment_id = prediction_row["experiment_id"]

            vote_traces_path = (
                PROJECT_ROOT
                / "artifacts"
                / f"experiment_{experiment_id}"
                / "consensus"
                / "vote_traces.json"
            )

            if not vote_traces_path.is_file():
                st.info("Prediction traces are not available for this experiment.")
            else:
                try:
                    vote_traces = json.loads(vote_traces_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    vote_traces = []

                if not vote_traces:
                    st.info("No prediction traces were recorded for this experiment.")
                else:
                    table_column, panel_column = st.columns([2.4, 1])

                    with table_column:
                        st.markdown("**Test set predictions**")
                        st.caption("View the predictions of each client and the final majority vote.")

                        hypothesis_names = [vote["hypothesis"] for vote in vote_traces[0]["votes"]]

                        table_rows = []
                        for index, trace in enumerate(vote_traces, start=1):
                            row_data = {
                                "#": index,
                                "Example": trace["example_id"],
                                "Truth": trace["true_label"],
                            }
                            for vote in trace["votes"]:
                                row_data[vote["hypothesis"]] = vote["prediction"]
                            row_data["Votes"] = f"{trace['positive_votes']}/{trace['number_of_voters']}"
                            row_data["Prediction"] = trace["prediction"]
                            row_data["Result"] = "✓" if trace["correct"] else "✕"
                            table_rows.append(row_data)

                        predictions_df = pd.DataFrame(table_rows)
                        styled_columns = ["Truth", *hypothesis_names, "Prediction"]
                        styled_df = predictions_df.style.map(style_pos_neg, subset=styled_columns)

                        st.dataframe(styled_df, use_container_width=True, hide_index=True, height=360)

                    with panel_column:
                        trace_by_example = {
                            str(trace["example_id"]): trace for trace in vote_traces
                        }
                        selected_example_id = st.selectbox(
                            "Example",
                            options=list(trace_by_example.keys()),
                            format_func=lambda example_id: f"Example {example_id}",
                            key=f"consensus_example_{experiment_id}",
                        )
                        trace = trace_by_example[selected_example_id]

                        with st.container(border=True):
                            st.markdown(f"**Example {trace['example_id']}**")
                            st.caption("How was this decision made?")
                            st.write("")

                            truth_col, pred_col = st.columns(2)
                            with truth_col:
                                st.caption("Ground truth")
                                st.markdown(render_vote_badge(trace["true_label"] == "POS"), unsafe_allow_html=True)
                            with pred_col:
                                st.caption("Final prediction")
                                st.markdown(render_vote_badge(trace["prediction"] == "POS"), unsafe_allow_html=True)

                            st.write("")
                            st.caption("Client votes")

                            for vote in trace["votes"]:
                                vote_label_col, vote_badge_col = st.columns([1, 1])
                                with vote_label_col:
                                    st.markdown(f"**{vote['hypothesis']}**")
                                with vote_badge_col:
                                    st.markdown(
                                        render_vote_badge(vote["prediction"] == "POS"),
                                        unsafe_allow_html=True,
                                    )
                                # Which rules of this hypothesis cover the
                                # example (absent in runs made before the
                                # rule-level traceability was added).
                                for rule_index, rule_text in zip(
                                    vote.get("rules_fired", []),
                                    vote.get("rules_text", []),
                                ):
                                    st.code(f"rule {rule_index}: {rule_text}", language="prolog")

                            st.write("")
                            st.caption(
                                f"Positive votes: **{trace['positive_votes']}/{trace['number_of_voters']}** "
                                f"— majority required: **{trace['required_majority']}**"
                            )
                            st.markdown(
                                f"**{trace['positive_votes']} {'≥' if trace['positive_votes'] >= trace['required_majority'] else '<'} "
                                f"{trace['required_majority']} → {trace['prediction']}**"
                            )

# --- Clients tab ----------------------------------------------------------

with tab_clients:
    if metadata["approach"] == "consensus":
        st.info(
            "Consensus clients learn independently — there's no shared "
            "federated evaluation to show here. See **Models** for each "
            "client's hypothesis and vote, and **Dataset** for their local "
            "data."
        )

        # Coverage of every hypothesis H_i on each client's own training data.
        if runs:
            if len(runs) > 1:
                coverage_run_number = st.selectbox(
                    "Run",
                    options=[r["run_number"] for r in runs],
                    format_func=lambda n: f"Run {n}",
                    key="consensus_coverage_run_picker",
                )
                coverage_row = next(r for r in runs if r["run_number"] == coverage_run_number)
            else:
                coverage_row = runs[0]

            analysis_path = (
                PROJECT_ROOT
                / "artifacts"
                / f"experiment_{coverage_row['experiment_id']}"
                / "consensus"
                / "consensus_analysis.json"
            )

            local_coverage = {}
            client_times: dict = {}
            client_uploads: dict = {}
            if analysis_path.is_file():
                try:
                    client_analysis = json.loads(
                        analysis_path.read_text(encoding="utf-8")
                    )
                    local_coverage = client_analysis.get("local_coverage", {})
                    client_times = client_analysis.get("induction_time_per_client", {}) or {}
                    client_uploads = (
                        (client_analysis.get("communication") or {}).get("upload_bytes_per_client", {})
                        or {}
                    )
                except (OSError, json.JSONDecodeError):
                    local_coverage = {}

            if client_times:
                with st.container(border=True):
                    st.markdown(
                        '<div class="section-title">Learning time per client</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        "Time each client spent learning its local hypothesis. "
                        "A client that reached the timeout is shown with a time "
                        "close to the limit (its hypothesis may be empty)."
                    )
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {
                                    "Client": client_id,
                                    "Learning time (s)": float(client_times[client_id]),
                                    "Hypothesis sent (KB)": float(client_uploads.get(client_id, 0.0)) / 1024,
                                }
                                for client_id in sorted(
                                    client_times,
                                    key=lambda c: int(c) if str(c).isdigit() else 0,
                                )
                            ]
                        ),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Learning time (s)": st.column_config.NumberColumn(format="%.1f"),
                            "Hypothesis sent (KB)": st.column_config.NumberColumn(format="%.2f"),
                        },
                    )

            if not local_coverage:
                st.info(
                    "Hypothesis coverage per client is not available for "
                    "this run (it is recorded by runs made with the latest "
                    "version)."
                )
            else:
                coverage_table = []
                for client_id in sorted(local_coverage, key=lambda c: int(c) if str(c).isdigit() else 0):
                    for item in local_coverage[client_id]:
                        positives = item["tp"] + item["fn"]
                        negatives = item["tn"] + item["fp"]
                        coverage_table.append(
                            {
                                "Client": client_id,
                                "Hypothesis": item["hypothesis"],
                                "Positives covered": f"{item['tp']} / {positives}",
                                "Negatives covered": f"{item['fp']} / {negatives}",
                                "Accuracy": (
                                    (item["tp"] + item["tn"]) / (positives + negatives)
                                    if (positives + negatives)
                                    else 0.0
                                ),
                            }
                        )

                with st.container(border=True):
                    st.markdown(
                        '<div class="section-title">Hypothesis coverage per client</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        "Each hypothesis H1, H2, ... evaluated on every "
                        "client's own training data. A client's own "
                        "hypothesis should fit its data best; the others "
                        "show how much the clients' data differ."
                    )
                    st.dataframe(
                        pd.DataFrame(coverage_table),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Accuracy": st.column_config.NumberColumn(format="%.3f"),
                        },
                    )
    elif not client_results:
        st.info("No client-level results are available for this benchmark.")
    else:
        available_runs = sorted({int(row["run_number"]) for row in client_results})

        selected_run = st.selectbox(
            "Run to inspect",
            options=available_runs,
            format_func=lambda run: f"Run {run}",
            key="client_results_run",
        )

        selected_client_results = [
            row for row in client_results if int(row["run_number"]) == selected_run
        ]

        total_examples = sum(int(r["number_of_examples"]) for r in selected_client_results)
        total_positive = sum(
            int(r["number_of_positive_examples"]) for r in selected_client_results
        )
        total_negative = sum(
            int(r["number_of_negative_examples"]) for r in selected_client_results
        )
        total_evaluations = sum(
            int(r["number_of_evaluations"]) for r in selected_client_results
        )

        render_metric_grid(
            [
                {"label": "Clients", "value": str(len(selected_client_results))},
                {"label": "Total examples", "value": str(total_examples)},
                {
                    "label": "Positive / Negative",
                    "value": f"{total_positive} / {total_negative}",
                },
                {"label": "Local evaluations", "value": str(total_evaluations)},
            ]
        )

        st.write("")

        with st.container(border=True):
            st.markdown('<div class="section-title">Per-client detail</div>', unsafe_allow_html=True)

            client_df = pd.DataFrame(
                [
                    {
                        "Client": (
                            "0 (centralized)" if is_client_zero else row["client_id"]
                        ),
                        "Partition": row["dataset_partition"],
                        "Examples": row["number_of_examples"],
                        "Positive": row["number_of_positive_examples"],
                        "Negative": row["number_of_negative_examples"],
                        "Evaluations": row["number_of_evaluations"],
                        "Avg wall (s)": row["average_eval_wall"],
                        "Score": row["final_score"],
                        "TP": row["tp"],
                        "FN": row["fn"],
                        "TN": row["tn"],
                        "FP": row["fp"],
                        "Accepted": bool(row["accepted_solution"]),
                    }
                    for row in selected_client_results
                ]
            )

            st.dataframe(
                client_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Avg wall (s)": st.column_config.NumberColumn(format="%.3f"),
                    "Accepted": st.column_config.CheckboxColumn(),
                },
            )

        chart_left, chart_right = st.columns(2)

        with chart_left:
            with st.container(border=True):
                st.markdown(
                    '<div class="section-title">Example distribution</div>',
                    unsafe_allow_html=True,
                )
                distribution_long = pd.DataFrame(
                    [
                        {
                            "Client": "C0 (centralized)" if is_client_zero else f"C{row['client_id']}",
                            "Type": kind,
                            "Count": row[key],
                        }
                        for row in selected_client_results
                        for kind, key in (
                            ("Positive", "number_of_positive_examples"),
                            ("Negative", "number_of_negative_examples"),
                        )
                    ]
                )
                st.altair_chart(
                    altair_bar(distribution_long, "Client", "Count", "Type"),
                    use_container_width=True,
                )

        with chart_right:
            with st.container(border=True):
                st.markdown(
                    '<div class="section-title">Local evaluation outcome</div>',
                    unsafe_allow_html=True,
                )
                performance_long = pd.DataFrame(
                    [
                        {"Client": "C0 (centralized)" if is_client_zero else f"C{row['client_id']}", "Type": kind, "Count": row[key]}
                        for row in selected_client_results
                        for kind, key in (
                            ("TP", "tp"),
                            ("TN", "tn"),
                            ("FP", "fp"),
                            ("FN", "fn"),
                        )
                    ]
                )
                st.altair_chart(
                    altair_bar(performance_long, "Client", "Count", "Type"),
                    use_container_width=True,
                )

        # Per-clause coverage of the final program on each client's local
        # data (FedMDL).
        coverage_rows = []
        for row in selected_client_results:
            raw = row.get("clause_coverage")
            if not raw:
                continue
            try:
                clauses = json.loads(raw)
            except (TypeError, ValueError):
                continue
            for index, clause in enumerate(clauses, start=1):
                coverage_rows.append(
                    {
                        "Client": row["client_id"],
                        "Clause #": index,
                        "Clause": clause.get("clause", ""),
                        "Positives covered": clause.get("positive_covered", 0),
                        "of positives": row["number_of_positive_examples"],
                        "Negatives covered": clause.get("negative_covered", 0),
                        "of negatives": row["number_of_negative_examples"],
                    }
                )

        if coverage_rows:
            with st.container(border=True):
                st.markdown(
                    '<div class="section-title">Clause coverage per client</div>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    "How many of each client's local examples every clause of "
                    "the final program covers."
                )
                st.dataframe(
                    pd.DataFrame(coverage_rows),
                    use_container_width=True,
                    hide_index=True,
                )

# --- Hypotheses tab (Coordination) -----------------------------------------

if metadata["approach"] in ("coordination", "collaboration"):
    with tab_hypotheses:
        from apps.hypothesis_tab import render_hypothesis_tab

        render_hypothesis_tab(selected_benchmark_id, federated_of, is_client_zero)

# --- Dataset explorer tab ---------------------------------------------------

with tab_dataset:
    if not client_results:
        st.info("No client-level results are available for this benchmark.")
    else:
        available_runs_ds = sorted({int(row["run_number"]) for row in client_results})

        run_col, client_col = st.columns(2)

        with run_col:
            selected_run_ds = st.selectbox(
                "Run",
                options=available_runs_ds,
                format_func=lambda run: f"Run {run}",
                key="dataset_explorer_run",
            )

        run_client_results = [
            row for row in client_results if int(row["run_number"]) == selected_run_ds
        ]
        client_options = {int(row["client_id"]): row for row in run_client_results}

        with client_col:
            selected_client_id = st.selectbox(
                "Client",
                options=sorted(client_options),
                format_func=lambda client_id: f"Client {client_id}",
                key="dataset_explorer_client",
            )

        selected_client = client_options[selected_client_id]
        partition_path = selected_client["dataset_partition"]
        partition_content = load_partition_content(partition_path)
        positive_examples, negative_examples = split_examples(partition_content["examples"])

        render_metric_grid(
            [
                {"label": "Positive examples", "value": str(len(positive_examples))},
                {"label": "Negative examples", "value": str(len(negative_examples))},
                {
                    "label": "Total examples",
                    "value": str(len(positive_examples) + len(negative_examples)),
                },
            ]
        )

        st.write("")

        ex_tab, bk_tab, bias_tab = st.tabs(["Examples", "Background knowledge", "Bias"])

        with ex_tab:
            pos_col, neg_col = st.columns(2)
            with pos_col:
                st.caption(f"Positive ({len(positive_examples)})")
                st.code("\n".join(positive_examples) or "—", language="prolog")
            with neg_col:
                st.caption(f"Negative ({len(negative_examples)})")
                st.code("\n".join(negative_examples) or "—", language="prolog")

        with bk_tab:
            st.code(partition_content["background_knowledge"] or "—", language="prolog")

        with bias_tab:
            st.code(partition_content["bias"] or "—", language="prolog")


st.markdown(
    '<div style="margin-top:auto; padding-top:1.2rem; border-top:1px solid #E5E7EB; color:#5B6472; font-size:0.85rem;">© Yasmine Akaichi · FILP Platform</div>',
    unsafe_allow_html=True,
)

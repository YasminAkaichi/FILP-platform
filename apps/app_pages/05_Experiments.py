from __future__ import annotations
import json
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


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Experiments | FILP",
    page_icon=":material/science:",
    layout="wide",
)

if hasattr(st, "logo"):
    try:
        st.logo(str(PROJECT_ROOT / "assets" / "filp_wordmark_white.svg"), size="large")
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
    # Dark sidebar
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

METHOD_STYLE = {
    "consensus": ("#7C5CFC", "#EFEAFE", "Consensus"),
    "collaboration": ("#3E7BFA", "#E8F0FE", "Collaboration"),
    "coordination": ("#E08A2B", "#FCEEDD", "Coordination"),
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
) -> alt.LayerChart:
    total = data[value].sum()

    arc = (
        alt.Chart(data)
        .mark_arc(innerRadius=58, outerRadius=95, cornerRadius=3, padAngle=0.01)
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
        .mark_text(size=24, fontWeight="bold", color=PALETTE["text"])
        .encode(text="text:N")
    )

    return alt.layer(arc, center_text).properties(height=230)


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
                status
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
                sr.solution
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
                cr.fp
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
            options=["All methods", "Consensus", "Collaboration", "Coordination"],
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
            options=["All statuses", "Completed", "Running", "Failed"],
            label_visibility="collapsed",
        )

    filtered_benchmarks = [
        b
        for b in all_benchmarks
        if (
            not search_query
            or search_query.lower() in b["name"].lower()
            or search_query.lower() in b["dataset"].lower()
        )
        and (method_filter == "All methods" or b["approach"] == method_filter.lower())
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

    if not page_rows:
        st.info("No experiment matches your filters.")
    else:
        COLUMN_WIDTHS = [0.6, 1.5, 1.1, 1.0, 0.6, 1.0, 1.0, 0.9]

        head_columns = st.columns(COLUMN_WIDTHS)
        for head_column, label in zip(
            head_columns,
            ["ID", "Name", "Method", "Dataset", "Clients", "Status", "Date", "Actions"],
        ):
            with head_column:
                st.markdown(f'<div class="table-head">{label}</div>', unsafe_allow_html=True)

        for benchmark in page_rows:
            row_columns = st.columns(COLUMN_WIDTHS)

            with row_columns[0]:
                st.markdown(f"**#{benchmark['id']}**")
            with row_columns[1]:
                st.write(benchmark.get("name") or "—")
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

        st.write("")
        st.caption(
            f"Showing {len(page_rows)} of {len(filtered_benchmarks)} experiments"
        )

        if total_pages > 1:
            pagination_columns = st.columns([0.6] + [0.5] * total_pages + [0.6] + [6])

            with pagination_columns[0]:
                if st.button("◀", disabled=(current_page <= 1), key="page_prev"):
                    st.session_state["experiments_page"] = current_page - 1
                    st.rerun()

            for offset, page_number in enumerate(range(1, total_pages + 1), start=1):
                with pagination_columns[offset]:
                    if st.button(
                        str(page_number),
                        key=f"page_{page_number}",
                        type="primary" if page_number == current_page else "secondary",
                    ):
                        st.session_state["experiments_page"] = page_number
                        st.rerun()

            with pagination_columns[total_pages + 1]:
                if st.button("▶", disabled=(current_page >= total_pages), key="page_next"):
                    st.session_state["experiments_page"] = current_page + 1
                    st.rerun()

    st.stop()


# =======================================================================
# DETAIL VIEW
# =======================================================================

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

    st.markdown(
        f'<div style="font-size:2rem; font-weight:750; color:{PALETTE["text"]}; '
        f'line-height:1.25;">Learning by {approach_label}</div>'
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

st.write("")

is_consensus_approach = metadata["approach"] == "consensus"

if is_consensus_approach:
    tab_overview, tab_models, tab_predictions, tab_clients, tab_dataset = st.tabs(
        ["Overview", "Models", "Predictions", "Clients", "🔍 Dataset"]
    )
else:
    tab_overview, tab_models, tab_clients, tab_dataset = st.tabs(
        ["Overview", "Models", "Clients", "🔍 Dataset"]
    )
    tab_predictions = None

# --- Overview tab ------------------------------------------------------

with tab_overview:
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
                    {"label": "Popper core", "value": f"{fmt(summary.popper_time.mean)} s", "sub": f"± {fmt(summary.popper_time.std)} s"},
                ]
            )

            with st.expander("ℹ️ What do these timings mean?"):
                st.markdown(
                    "- **Startup time** — spinning up the federated server and "
                    "connecting all clients before learning starts.\n"
                    "- **Popper core** — time spent purely in Popper's "
                    "generate-test-constrain search, excluding federation "
                    "overhead.\n"
                    "- **Learning time** — the full federated loop: "
                    "broadcasting hypotheses, waiting on clients, aggregating "
                    "feedback, and the Popper core time above.\n"
                    "- **End-to-end time** — startup + learning, the total "
                    "wall-clock time for the run."
                )

        st.write("")

        outcome_left, outcome_right, outcome_info = st.columns([1, 1.1, 1])

        with outcome_left:
            with st.container(border=True):
                st.markdown('<div class="section-title">Learning outcome</div>', unsafe_allow_html=True)
                st.markdown(f"🔄 &nbsp; **{fmt(summary.number_of_rounds.mean, 1)}** rounds")
                st.markdown(f"🧩 &nbsp; **{fmt(summary.number_of_programs.mean, 1)}** programs explored")
                st.markdown(f"🏆 &nbsp; **{fmt(summary.final_score.mean, 2)}** final score")
                st.caption(
                    "Averaged across all runs in this benchmark. See the "
                    "Models tab for the hypothesis and per-client contribution."
                )

        latest_run_number = runs[-1]["run_number"] if runs else None
        latest_client_rows = [
            row
            for row in client_results
            if latest_run_number is not None and int(row["run_number"]) == latest_run_number
        ]
        accepted_count = sum(1 for row in latest_client_rows if row["accepted_solution"])
        not_accepted_count = len(latest_client_rows) - accepted_count

        with outcome_right:
            with st.container(border=True):
                st.markdown('<div class="section-title">Client acceptance</div>', unsafe_allow_html=True)
                if latest_client_rows:
                    acceptance_data = pd.DataFrame(
                        {
                            "Outcome": ["Accepted", "Not accepted"],
                            "Count": [accepted_count, not_accepted_count],
                        }
                    )
                    acceptance_colors = {
                        "Accepted": PALETTE["success"],
                        "Not accepted": PALETTE["error"],
                    }
                    st.altair_chart(
                        altair_donut(acceptance_data, "Outcome", "Count", acceptance_colors),
                        use_container_width=True,
                    )
                else:
                    st.info("No client-level results available for this run.")

        with outcome_info:
            with st.container(border=True):
                st.markdown('<div class="section-title">Run information</div>', unsafe_allow_html=True)
                render_kv_rows(
                    [
                        ("Status", render_badge(metadata["status"])),
                        ("Total time", f"{fmt(summary.total_time.mean)} s"),
                        ("Runs", str(summary.number_of_runs)),
                        ("Max rounds", str(metadata.get("rounds") or "—")),
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
                model_columns = st.columns(len(hypotheses))

                for column, (index, hypothesis) in zip(model_columns, enumerate(hypotheses, start=1)):
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

                contribution_columns = st.columns(len(run_client_rows))

                for column, client_row in zip(contribution_columns, run_client_rows):
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
                        "Client": row["client_id"],
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
                            "Client": f"C{row['client_id']}",
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
                        {"Client": f"C{row['client_id']}", "Type": kind, "Count": row[key]}
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

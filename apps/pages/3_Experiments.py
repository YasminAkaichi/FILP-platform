from __future__ import annotations
import json
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


from core.benchmark import BenchmarkConfig
from core.benchmark_launcher import BenchmarkLauncher
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
    page_icon="",
    layout="wide",
)

# Same logo, same fixed slot above the sidebar navigation on every page.
LOGO_PATH = PROJECT_ROOT / "assets" / "filp_logo.svg"

if hasattr(st, "logo"):
    try:
        st.logo(str(LOGO_PATH), size="large")
    except Exception:
        pass


# ---------------------------------------------------------------------
# Visual design system
# ---------------------------------------------------------------------
#
# A soft, low-contrast palette. Nothing pure white / pure red / pure
# green — everything is muted so the page can be scanned for a while
# without eye strain. All colors live here so the rest of the page
# only ever refers to a name, not a hex code.

PALETTE = {
    "bg_card": "#F6F8FC",
    "border": "#E2E8F5",
    "text_muted": "#5B6472",
    "text": "#1F2430",
    "primary": "#5B7FDE",
    "primary_soft": "#EAF0FE",
    "success": "#2F9E63",
    "success_soft": "#E7F6EE",
    "warning": "#C98A1F",
    "warning_soft": "#FCF1DE",
    "error": "#D1554B",
    "error_soft": "#FBEAE8",
    "neutral": "#8A93A3",
    "neutral_soft": "#EEF1F6",
}

CHART_COLORS = ["#5B7FDE", "#7FB88F", "#E8A85C", "#C97BB0", "#6BB6C9", "#B99BD8"]

STATUS_STYLE = {
    "completed": (PALETTE["success"], PALETTE["success_soft"], "✓"),
    "success": (PALETTE["success"], PALETTE["success_soft"], "✓"),
    "running": (PALETTE["primary"], PALETTE["primary_soft"], "●"),
    "pending": (PALETTE["neutral"], PALETTE["neutral_soft"], "○"),
    "queued": (PALETTE["neutral"], PALETTE["neutral_soft"], "○"),
    "failed": (PALETTE["error"], PALETTE["error_soft"], "✕"),
    "error": (PALETTE["error"], PALETTE["error_soft"], "✕"),
}


def inject_style() -> None:
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-feature-settings: "tnum";
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

        /* Status badge */
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

        code, .stCode {{
            font-size: 0.82rem !important;
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


# ---------------------------------------------------------------------
# Data access helpers (unchanged behaviour, same queries)
# ---------------------------------------------------------------------

def load_benchmark_metadata(benchmark_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                name,
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


def load_recent_benchmarks(limit: int = 30) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                name,
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
# New benchmark form (rendered inline in a dialog, or in an expander
# as a fallback on older Streamlit versions without st.dialog)
# ---------------------------------------------------------------------

def launch_benchmark(
    approach: str,
    dataset: str,
    number_of_clients: int,
    partition_strategy: str,
    number_of_runs: int,
    base_seed: int,
    benchmark_name: str,
    rounds: int = 35000,
    learner: str = "popper",
    timeout: int = 600,
) -> None:
    config = BenchmarkConfig(
        name=benchmark_name.strip(),
        approach=approach,
        dataset=dataset,
        number_of_clients=int(number_of_clients),
        partition_strategy=partition_strategy,
        number_of_runs=int(number_of_runs),
        base_seed=int(base_seed),
        learner=learner,
        rounds=int(rounds),
        timeout=int(timeout),
        server_address="localhost:8080",
    )

    try:
        with st.status("Running benchmark…", expanded=True) as status:
            chips = [
                ("Dataset", dataset),
                ("Clients", str(number_of_clients)),
                ("Partition", partition_strategy),
                ("Runs", str(number_of_runs)),
            ]
            if approach == "consensus":
                chips.append(("Learner", learner.title()))
            else:
                chips.append(("Max rounds", str(rounds)))
            render_chips(chips)

            launcher = BenchmarkLauncher()
            benchmark_id = launcher.run(config)

            st.session_state["selected_benchmark_id"] = benchmark_id

            status.update(
                label=f"Benchmark {benchmark_id} completed",
                state="complete",
                expanded=False,
            )

        st.toast(f"Benchmark {benchmark_id} completed successfully.", icon="✅")
        st.session_state["_just_launched"] = True
        st.rerun()

    except Exception as error:
        st.error(f"Benchmark failed: {error}")


def render_how_it_works() -> None:
    st.markdown(
        "A logical dataset is split across several **clients**. In "
        "Collaboration and Coordination, clients keep their examples private "
        "and only exchange symbolic feedback with a server until the group "
        "converges on one shared program. In Consensus, each client learns "
        "its own local program independently, and the final label is decided "
        "by majority vote."
    )

    st.write("")

    concept_left, concept_right = st.columns(2)

    with concept_left:
        with st.container(border=True):
            st.markdown("**📚 Dataset**")
            st.caption(
                "The logical data (positive / negative examples + background "
                "knowledge) the clients will learn from. Each dataset hides "
                "its own target rule to discover."
            )
        with st.container(border=True):
            st.markdown("**🔀 Partition strategy**")
            st.caption(
                "IID: examples are split evenly and randomly across clients — "
                "the easy case. Non-IID: the split is uneven / skewed, closer "
                "to real-world conditions and harder to learn from."
            )

    with concept_right:
        with st.container(border=True):
            st.markdown("**👥 Number of clients**")
            st.caption(
                "How many participants hold a partition of the dataset. More "
                "clients means more parallelism, but also more coordination "
                "between them (or, in Consensus, more votes)."
            )
        with st.container(border=True):
            st.markdown("**🔁 Runs & seed**")
            st.caption(
                "Runs repeat the experiment with different seeds to measure "
                "robustness (mean ± std). Collaboration and Coordination also "
                "cap the number of federated rounds; Consensus caps how long "
                "each client's local learner is allowed to run instead."
            )


APPROACH_OPTIONS = {
    "collaboration": {"label": "Learning by Collaboration", "available": True},
    "coordination": {"label": "Learning by Coordination", "available": True},
    "consensus": {"label": "Learning by Consensus", "available": True},
}


def render_new_benchmark_form() -> None:
    st.caption("Choose an approach, then configure your setup.")

    # Outside the form on purpose: st.form() only reruns on submit, but we
    # need the page to react immediately when the approach changes (to
    # show/hide the config fields below).
    approach = st.selectbox(
        "Approach to test",
        options=list(APPROACH_OPTIONS.keys()),
        format_func=lambda key: (
            f"{APPROACH_OPTIONS[key]['label']}"
            + ("" if APPROACH_OPTIONS[key]["available"] else " — coming soon")
        ),
        help=(
            "Collaboration and Coordination federate a single search across "
            "the clients. Consensus lets each client learn on its own and "
            "combines the results by majority vote — its setup is a bit "
            "different."
        ),
    )

    if not APPROACH_OPTIONS[approach]["available"]:
        st.info(
            f"**{APPROACH_OPTIONS[approach]['label']}** isn't implemented in FILP "
            "yet, so there's nothing to configure here for it. See the Approaches "
            "page for what's planned."
        )
        st.page_link("pages/1_Approaches.py", label="View the research roadmap")
        return

    is_consensus = approach == "consensus"

    with st.form("benchmark_form"):
        column_1, column_2 = st.columns(2)

        with column_1:
            dataset = st.selectbox(
                "Dataset",
                options=["zendo1", "trains1", "trains2", "trains3"],
                index=0,
                help="The logical dataset (examples + background knowledge) the clients will learn from.",
            )
            number_of_clients = st.selectbox(
                "Number of clients",
                options=[2, 3, 10],
                index=1,
                help=(
                    "How many participants hold a partition of the dataset "
                    "and vote on the final label."
                    if is_consensus
                    else "How many participants hold a partition of the dataset and collaborate."
                ),
            )
            partition_strategy = st.selectbox(
                "Partition strategy",
                options=["iid", "non_iid"],
                index=0,
                help="IID = even random split. Non-IID = uneven / skewed split, closer to real conditions.",
            )

        with column_2:
            number_of_runs = st.number_input(
                "Number of runs",
                min_value=1,
                max_value=20,
                value=1,
                step=1,
                help="Repeats the experiment with different seeds to measure robustness (mean ± std).",
            )
            base_seed = st.number_input(
                "Base seed",
                min_value=0,
                value=42,
                step=1,
                help="Starting random seed. Each run uses base_seed + run index, so results stay reproducible.",
            )

            if is_consensus:
                learner = st.selectbox(
                    "Local learner",
                    options=["popper", "andante"],
                    format_func=lambda key: "Popper" if key == "popper" else "Andante",
                    help="The ILP engine each client uses to learn its own local hypothesis.",
                )
                timeout = st.number_input(
                    "Local learner timeout (seconds)",
                    min_value=10,
                    value=600,
                    step=30,
                    help="Safety cap on how long each client's local learner is allowed to run before it stops.",
                )
                rounds = 35000  # unused for Consensus, kept as a harmless default
            else:
                learner = "popper"
                timeout = 600  # unused for Collaboration / Coordination
                rounds = st.number_input(
                    "Maximum rounds",
                    min_value=1,
                    value=35000,
                    step=100,
                    help="Safety cap on federated learning rounds before the run stops.",
                )

        default_name = f"{dataset}_{approach}_k{number_of_clients}_{partition_strategy}"
        benchmark_name = st.text_input("Benchmark name", value=default_name)

        if is_consensus:
            recap = (
                '<div class="section-caption">You are about to run '
                f"<b>{number_of_runs}</b> run(s) on <b>{dataset}</b>, split "
                f"<b>{partition_strategy.upper()}</b> across <b>{number_of_clients}</b> "
                f"clients, each learning locally with <b>{learner.title()}</b>.</div>"
            )
        else:
            recap = (
                '<div class="section-caption">You are about to run '
                f"<b>{number_of_runs}</b> run(s) on <b>{dataset}</b>, split "
                f"<b>{partition_strategy.upper()}</b> across <b>{number_of_clients}</b> "
                "clients.</div>"
            )

        st.markdown(recap, unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "🚀 Run benchmark", type="primary", use_container_width=True
        )

    if submitted:
        launch_benchmark(
            approach=approach,
            dataset=dataset,
            number_of_clients=number_of_clients,
            partition_strategy=partition_strategy,
            number_of_runs=number_of_runs,
            base_seed=base_seed,
            rounds=rounds,
            learner=learner,
            timeout=timeout,
            benchmark_name=benchmark_name,
        )


if hasattr(st, "dialog"):
    _new_benchmark_dialog = st.dialog("New benchmark", width="large")(
        render_new_benchmark_form
    )
else:
    _new_benchmark_dialog = None


# ---------------------------------------------------------------------
# Page body
# ---------------------------------------------------------------------

inject_style()

st.title("Experiments")
st.caption(
    "Configure and launch Learning by Collaboration runs, "
    "then explore the aggregated and per-run results."
)

with st.expander("🧭 How does a collaborative experiment work?", expanded=True):
    render_how_it_works()

recent_benchmarks = load_recent_benchmarks()

# --- Sidebar: launcher + benchmark picker --------------------------------

with st.sidebar:
    st.markdown('<div class="section-title">Benchmarks</div>', unsafe_allow_html=True)

    if st.button("＋ New benchmark", type="primary", use_container_width=True):
        if _new_benchmark_dialog is not None:
            _new_benchmark_dialog()
        else:
            st.session_state["_show_inline_form"] = True

    if _new_benchmark_dialog is None and st.session_state.get("_show_inline_form"):
        with st.expander("New benchmark", expanded=True):
            render_new_benchmark_form()

    st.page_link("pages/2_Datasets.py", label="Explore datasets")

    st.divider()

    if not recent_benchmarks:
        st.info("No benchmark has been recorded yet. Launch one above.")
        st.stop()

    search_query = st.text_input(
        "Filter", placeholder="Search by name or dataset…", label_visibility="collapsed"
    )

    filtered_benchmarks = [
        row
        for row in recent_benchmarks
        if not search_query
        or search_query.lower() in row["name"].lower()
        or search_query.lower() in row["dataset"].lower()
    ] or recent_benchmarks

    benchmark_labels = {
        row["id"]: f"#{row['id']} · {row['name']}" for row in filtered_benchmarks
    }

    selected_experiment_id = st.session_state.get("selected_experiment_id")
    benchmark_from_experiment = None

    if selected_experiment_id is not None:
        benchmark_from_experiment = find_benchmark_id_by_experiment(selected_experiment_id)

    default_benchmark_id = benchmark_from_experiment or st.session_state.get(
        "selected_benchmark_id", filtered_benchmarks[0]["id"]
    )

    benchmark_ids = list(benchmark_labels.keys())

    if default_benchmark_id not in benchmark_ids:
        default_benchmark_id = benchmark_ids[0]

    selected_benchmark_id = st.radio(
        "Recent runs",
        options=benchmark_ids,
        format_func=lambda benchmark_id: benchmark_labels[benchmark_id],
        index=benchmark_ids.index(default_benchmark_id),
        label_visibility="collapsed",
    )

    st.session_state["selected_benchmark_id"] = selected_benchmark_id
    st.session_state.pop("selected_experiment_id", None)


# --- Main area: results for the selected benchmark ------------------------

metadata = load_benchmark_metadata(selected_benchmark_id)

if metadata["approach"] == "consensus":
    summary = load_consensus_benchmark_summary(
        selected_benchmark_id
    )
    runs = load_consensus_benchmark_runs(
        selected_benchmark_id
    )
    client_results = []
else:
    summary = load_benchmark_summary(
        selected_benchmark_id
    )
    runs = load_benchmark_runs(
        selected_benchmark_id
    )
    client_results = load_client_results(
        selected_benchmark_id
    )


header_left, header_right = st.columns([5, 1])

with header_left:
    st.markdown(
        f'<div class="section-title" style="font-size:1.3rem;">{metadata["name"]}</div>',
        unsafe_allow_html=True,
    )
    header_chips = [
        ("Dataset", metadata["dataset"]),
        ("Clients", str(metadata["number_of_clients"])),
        ("Partition", metadata["partition_strategy"]),
        ("Runs", str(metadata["number_of_runs"])),
        ("Seed", str(metadata["base_seed"])),
    ]
    if metadata["approach"] == "consensus":
        header_chips.append(("Learner", str(metadata.get("learner") or "popper").title()))
    render_chips(header_chips)

with header_right:
    st.markdown(
        f'<div style="text-align:right; padding-top:6px;">{render_badge(metadata["status"])}</div>',
        unsafe_allow_html=True,
    )

st.write("")

(
    tab_overview,
    tab_runs,
    tab_hypotheses,
    tab_clients,
    tab_dataset,
) = st.tabs(
    [
        "📈 Overview",
        "Runs",
        "Hypotheses & predictions",
        "Clients",
        "🔍 Dataset explorer",
    ]
)
# --- Overview tab ----------------------------------------------------------

with tab_overview:
    if metadata["approach"] == "consensus":
        with st.container(border=True):
            st.markdown(
                '<div class="section-title">Consensus performance</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="section-caption">'
                'Global majority-vote performance on the shared test set'
                '</div>',
                unsafe_allow_html=True,
            )

            render_metric_grid(
                [
                    {
                        "label": "Accuracy",
                        "value": fmt(summary.accuracy.mean),
                        "sub": f"± {fmt(summary.accuracy.std)}",
                    },
                    {
                        "label": "Precision",
                        "value": fmt(summary.precision.mean),
                        "sub": f"± {fmt(summary.precision.std)}",
                    },
                    {
                        "label": "Recall",
                        "value": fmt(summary.recall.mean),
                        "sub": f"± {fmt(summary.recall.std)}",
                    },
                    {
                        "label": "F1",
                        "value": fmt(summary.f1.mean),
                        "sub": f"± {fmt(summary.f1.std)}",
                    },
                ]
            )

        with st.container(border=True):
            st.markdown(
                '<div class="section-title">Prediction outcome</div>',
                unsafe_allow_html=True,
            )

            render_metric_grid(
                [
                    {
                        "label": "True positives",
                        "value": fmt(summary.tp.mean, 1),
                    },
                    {
                        "label": "True negatives",
                        "value": fmt(summary.tn.mean, 1),
                    },
                    {
                        "label": "False positives",
                        "value": fmt(summary.fp.mean, 1),
                    },
                    {
                        "label": "False negatives",
                        "value": fmt(summary.fn.mean, 1),
                    },
                    {
                        "label": "Hypotheses",
                        "value": fmt(
                            summary.number_of_hypotheses.mean,
                            1,
                        ),
                    },
                ]
            )

    else:
        with st.container(border=True):
            st.markdown(
                '<div class="section-title">Timing</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="section-caption">'
                'Mean ± standard deviation across all runs'
                '</div>',
                unsafe_allow_html=True,
            )

            render_metric_grid(
                [
                    {
                        "label": "Learning time",
                        "value": f"{fmt(summary.learning_time.mean)} s",
                        "sub": f"± {fmt(summary.learning_time.std)} s",
                    },
                    {
                        "label": "Startup time",
                        "value": f"{fmt(summary.startup_time.mean)} s",
                        "sub": f"± {fmt(summary.startup_time.std)} s",
                    },
                    {
                        "label": "End-to-end time",
                        "value": f"{fmt(summary.total_time.mean)} s",
                        "sub": f"± {fmt(summary.total_time.std)} s",
                    },
                    {
                        "label": "Popper core",
                        "value": f"{fmt(summary.popper_time.mean)} s",
                        "sub": f"± {fmt(summary.popper_time.std)} s",
                    },
                ]
            )

        with st.container(border=True):
            st.markdown(
                '<div class="section-title">Learning outcome</div>',
                unsafe_allow_html=True,
            )

            render_metric_grid(
                [
                    {
                        "label": "Rounds",
                        "value": fmt(
                            summary.number_of_rounds.mean,
                            1,
                        ),
                        "sub": (
                            f"± {fmt(summary.number_of_rounds.std, 1)}"
                        ),
                    },
                    {
                        "label": "Programs explored",
                        "value": fmt(
                            summary.number_of_programs.mean,
                            1,
                        ),
                        "sub": (
                            f"± {fmt(summary.number_of_programs.std, 1)}"
                        ),
                    },
                    {
                        "label": "Final score",
                        "value": fmt(
                            summary.final_score.mean,
                            2,
                        ),
                        "sub": (
                            f"± {fmt(summary.final_score.std, 2)}"
                        ),
                    },
                ]
            )
# --- Runs tab ----------------------------------------------------------

with tab_runs:
    st.markdown(
        '<div class="section-title">Individual runs</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-caption">'
        'One row per run — sort any column by clicking its header'
        '</div>',
        unsafe_allow_html=True,
    )

    if metadata["approach"] == "consensus":
        runs_df = pd.DataFrame(
            [
                {
                    "Run": row["run_number"],
                    "Status": (
                        row["status"] or "unknown"
                    ).title(),
                    "Seed": row["random_seed"],
                    "Experiment": row["experiment_id"],
                    "Learner": row["learner"],
                    "Hypotheses": row[
                        "number_of_hypotheses"
                    ],
                    "Accuracy": row["accuracy"],
                    "Precision": row["precision"],
                    "Recall": row["recall"],
                    "F1": row["f1"],
                    "TP": row["tp"],
                    "TN": row["tn"],
                    "FP": row["fp"],
                    "FN": row["fn"],
                }
                for row in runs
            ]
        )

        st.dataframe(
            runs_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Accuracy": st.column_config.NumberColumn(
                    format="%.3f"
                ),
                "Precision": st.column_config.NumberColumn(
                    format="%.3f"
                ),
                "Recall": st.column_config.NumberColumn(
                    format="%.3f"
                ),
                "F1": st.column_config.NumberColumn(
                    format="%.3f"
                ),
            },
        )

    else:
        runs_df = pd.DataFrame(
            [
                {
                    "Run": row["run_number"],
                    "Status": (
                        row["status"] or "unknown"
                    ).title(),
                    "Seed": row["random_seed"],
                    "Experiment": row["experiment_id"],
                    "Learning (s)": row[
                        "learning_time_seconds"
                    ],
                    "Startup (s)": row[
                        "startup_time_seconds"
                    ],
                    "End-to-end (s)": row[
                        "total_time_seconds"
                    ],
                    "Popper (s)": row[
                        "popper_time_seconds"
                    ],
                    "Rounds": row["number_of_rounds"],
                    "Programs": row["number_of_programs"],
                    "Score": row["final_score"],
                }
                for row in runs
            ]
        )

        st.dataframe(
            runs_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Learning (s)": (
                    st.column_config.NumberColumn(
                        format="%.3f"
                    )
                ),
                "Startup (s)": (
                    st.column_config.NumberColumn(
                        format="%.3f"
                    )
                ),
                "End-to-end (s)": (
                    st.column_config.NumberColumn(
                        format="%.3f"
                    )
                ),
                "Popper (s)": (
                    st.column_config.NumberColumn(
                        format="%.3f"
                    )
                ),
                "Score": st.column_config.ProgressColumn(
                    format="%.2f",
                    min_value=0.0,
                    max_value=max(
                        [
                            r["final_score"]
                            for r in runs
                            if r["final_score"]
                        ]
                        or [1.0]
                    ),
                ),
            },
        )
# --- Hypotheses & predictions tab -------------------------------------------

with tab_hypotheses:
    st.markdown(
        '<div class="section-title">Hypotheses & predictions</div>',
        unsafe_allow_html=True,
    )

    # ================================================================
    # CONSENSUS — one hypothesis per client, plus how each one voted
    # ================================================================

    if metadata["approach"] == "consensus":
        st.markdown(
            '<div class="section-caption">'
            'Each client learns its own hypothesis; the final label is '
            'decided by majority vote.'
            '</div>',
            unsafe_allow_html=True,
        )

        if not runs:
            st.info("No Consensus runs available.")

        for row in runs:
            experiment_id = row["experiment_id"]

            with st.expander(
                f"Run {row['run_number']} · experiment #{experiment_id}",
                expanded=(len(runs) == 1),
            ):
                hypotheses_raw = row.get("hypotheses")

                try:
                    hypotheses = json.loads(hypotheses_raw) if hypotheses_raw else []
                except (json.JSONDecodeError, TypeError):
                    hypotheses = []

                if not hypotheses:
                    st.caption("No saved hypotheses for this experiment.")
                    continue

                # --- Client 1 / H1, Client 2 / H2, ... ---
                for index, hypothesis in enumerate(hypotheses, start=1):
                    st.markdown(f"**Client {index}** · H{index}")

                    if hypothesis:
                        st.code("\n".join(hypothesis), language="prolog")
                    else:
                        st.caption(
                            "Empty hypothesis — this client always votes "
                            "negative, but still counts towards the majority."
                        )

                # --- this run's predictions, if recorded ---
                vote_traces_path = (
                    PROJECT_ROOT
                    / "artifacts"
                    / f"experiment_{experiment_id}"
                    / "consensus"
                    / "vote_traces.json"
                )

                if not vote_traces_path.is_file():
                    st.caption(
                        "Prediction traces are not available for this experiment."
                    )
                    continue

                try:
                    vote_traces = json.loads(
                        vote_traces_path.read_text(encoding="utf-8")
                    )
                except (OSError, json.JSONDecodeError):
                    vote_traces = []

                if not vote_traces:
                    st.caption(
                        "No prediction traces were recorded for this experiment."
                    )
                    continue

                st.divider()
                st.markdown("**See how each client predicted on a test example**")

                trace_by_example = {
                    str(trace["example_id"]): trace for trace in vote_traces
                }

                selected_example_id = st.selectbox(
                    "Test example",
                    options=list(trace_by_example.keys()),
                    format_func=lambda example_id: f"Example {example_id}",
                    key=f"consensus_example_{experiment_id}",
                )

                trace = trace_by_example[selected_example_id]

                vote_columns = st.columns(len(trace["votes"]))

                for column, vote in zip(vote_columns, trace["votes"]):
                    with column:
                        client_number = vote["hypothesis"].lstrip("H")
                        st.caption(f"Client {client_number}")
                        st.markdown(
                            render_vote_badge(vote["prediction"] == "POS"),
                            unsafe_allow_html=True,
                        )

                st.write("")

                correct = trace["correct"]
                st.markdown(
                    f"**{trace['positive_votes']}/{trace['number_of_voters']}** "
                    f"clients predicted positive (at least "
                    f"**{trace['required_majority']}** needed for a majority) "
                    f"→ consensus predicts **{trace['prediction']}**. True "
                    f"label: **{trace['true_label']}** — "
                    + ("✓ correct." if correct else "✕ incorrect.")
                )

    # ================================================================
    # COLLABORATION / COORDINATION — one shared hypothesis, plus each
    # client's contribution to the aggregated outcome
    # ================================================================

    else:
        st.markdown(
            '<div class="section-caption">'
            "Final program produced by each run, and how each client's "
            'local evaluation contributed to it.'
            '</div>',
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

                for client_row in run_client_rows:
                    accepted = bool(client_row["accepted_solution"])
                    epsilon_positive = client_row["final_epsilon_positive"] or "—"
                    epsilon_negative = client_row["final_epsilon_negative"] or "—"
                    verdict = (
                        "accepted this hypothesis"
                        if accepted
                        else "did not fully accept it"
                    )

                    label_column, detail_column = st.columns([1, 4])

                    with label_column:
                        st.markdown(f"**Client {client_row['client_id']}**")

                    with detail_column:
                        st.caption(
                            f"Reported (ε+={epsilon_positive}, "
                            f"ε−={epsilon_negative}), score "
                            f"{client_row['final_score']} — {verdict}."
                        )
# --- Clients tab ----------------------------------------------------------

with tab_clients:
    if not client_results:
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

# --- Dataset explorer tab ----------------------------------------------------------

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

        st.caption(f"Partition: `{partition_path}`")

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
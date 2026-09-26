from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.benchmark import BenchmarkConfig
from core.benchmark_launcher import BenchmarkLauncher

DATASETS_DIRECTORY = PROJECT_ROOT / "datasets"


def get_available_datasets() -> list[str]:
    """
    Every real, learnable dataset under datasets/ — excludes the
    "generated" partitions folder and any already-partitioned
    "<name>_partN" directory, and requires exs.pl / bk.pl / bias.pl to
    actually be present (same rule as the Inductive Logic Programming
    page, kept in sync manually since each page is self-contained).
    """
    if not DATASETS_DIRECTORY.is_dir():
        return []
    return sorted(
        directory.name
        for directory in DATASETS_DIRECTORY.iterdir()
        if directory.is_dir()
        and directory.name != "generated"
        and "_part" not in directory.name
        and (directory / "exs.pl").is_file()
        and (directory / "bk.pl").is_file()
        and (directory / "bias.pl").is_file()
    )


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Simulation | FILP",
    page_icon=":material/play_circle:",
    layout="wide",
)

if hasattr(st, "logo"):
    try:
        st.logo(str(PROJECT_ROOT / "assets" / "filp_wordmark_white.svg"), size="large")
    except Exception:
        pass




# ---------------------------------------------------------------------
# Visual design system (same palette / dark sidebar as the Experiments
# page, duplicated here since each page injects its own style)
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
    "sidebar_active_bg": "#1B2A4C",
    "sidebar_border": "#22314F",
}


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
        [data-testid="stHeader"] {{
            background: transparent;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            border-radius: 14px !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 14px !important;
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

        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }}

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
        .chip b {{
            color: {PALETTE["text_muted"]};
            font-weight: 500;
            margin-right: 4px;
        }}

        /* Step indicator */
        .wizard-steps {{
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 6px;
        }}
        .wizard-step {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
        }}
        .wizard-step .dot {{
            width: 22px;
            height: 22px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.72rem;
            font-weight: 700;
            background: {PALETTE["neutral_soft"]};
            color: {PALETTE["text_muted"]};
        }}
        .wizard-step.active {{
            color: {PALETTE["text"]};
            font-weight: 600;
        }}
        .wizard-step.active .dot {{
            background: {PALETTE["primary"]};
            color: #FFFFFF;
        }}
        .wizard-step.done .dot {{
            background: {PALETTE["success"]};
            color: #FFFFFF;
        }}
        .wizard-arrow {{
            color: {PALETTE["border"]};
            margin: 0 2px;
        }}

        /* Method picker cards */
        .method-card-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {PALETTE["text"]};
            margin: 8px 0 4px 0;
        }}
        .method-card-desc {{
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 10px;
            min-height: 55px;
        }}
        .breadcrumb {{
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 4px;
        }}

        /* Make the whole method card clickable: the real button that
           follows the card's HTML is stretched over it (position
           absolute, fully transparent) instead of showing as its own
           button below the card. */
        div[class*="st-key-method_card_"] {{
            position: relative !important;
        }}
        div[class*="st-key-method_card_"] [data-testid="stButton"],
        div[class*="st-key-method_card_"] [data-testid="stElementContainer"]:has(button) {{
            position: absolute !important;
            inset: 0 !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            width: 100% !important;
            height: 100% !important;
            margin: 0 !important;
            z-index: 5 !important;
        }}
        div[class*="st-key-method_card_"] [data-testid="stButton"] button {{
            width: 100% !important;
            height: 100% !important;
            min-height: 100% !important;
            opacity: 0 !important;
            cursor: pointer !important;
            padding: 0 !important;
            margin: 0 !important;
            border: none !important;
        }}

        /* Dark sidebar, matching the Experiments page */
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
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_badge(text: str, kind: str = "neutral") -> str:
    colors = {
        "neutral": (PALETTE["neutral"], PALETTE["neutral_soft"]),
        "primary": (PALETTE["primary"], PALETTE["primary_soft"]),
        "success": (PALETTE["success"], PALETTE["success_soft"]),
        "warning": (PALETTE["warning"], PALETTE["warning_soft"]),
    }
    color, bg = colors.get(kind, colors["neutral"])
    return f'<span class="badge" style="color:{color};background:{bg};">{text}</span>'


def render_chips(pairs: list[tuple[str, str]]) -> None:
    chips = "".join(
        f'<span class="chip"><b>{label}</b>{value}</span>' for label, value in pairs
    )
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)


def render_step_indicator(current_step: int) -> None:
    steps = ["Method", "Parameters", "Review", "Run"]
    parts = []

    for index, label in enumerate(steps, start=1):
        state = "active" if index == current_step else ("done" if index < current_step else "")
        dot_content = "✓" if index < current_step else str(index)
        parts.append(
            f'<span class="wizard-step {state}"><span class="dot">{dot_content}</span>{label}</span>'
        )
        if index < len(steps):
            parts.append('<span class="wizard-arrow">→</span>')

    st.markdown(f'<div class="wizard-steps">{"".join(parts)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Approach catalogue
# ---------------------------------------------------------------------

_METHOD_ICON_COLOR = "#0F1B33"
_METHOD_ICON_ATTRS = (
    f'viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="{_METHOD_ICON_COLOR}" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
)

ICON_USERS = (
    f'<svg {_METHOD_ICON_ATTRS}><circle cx="9" cy="8" r="3"/>'
    '<path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/>'
    '<path d="M16 4.2c1.5.5 2.5 1.9 2.5 3.5s-1 3-2.5 3.5"/>'
    '<path d="M18.5 14.3c2.2.6 3.5 2.6 3.5 5.7"/></svg>'
)
ICON_LINK = (
    f'<svg {_METHOD_ICON_ATTRS}><path d="M9.5 14.5 14.5 9.5"/>'
    '<path d="M11 6.5 12.7 4.8a3.5 3.5 0 0 1 5 5L15.9 11.4"/>'
    '<path d="M13 17.5l-1.7 1.7a3.5 3.5 0 0 1-5-5l1.9-1.9"/></svg>'
)
ICON_GEAR = (
    f'<svg {_METHOD_ICON_ATTRS}><circle cx="12" cy="12" r="3.2"/>'
    '<path d="M12 3.5v2.2M12 18.3v2.2M20.5 12h-2.2M5.7 12H3.5"/>'
    '<path d="M17.8 6.2l-1.6 1.6M7.8 16.2l-1.6 1.6M17.8 17.8l-1.6-1.6M7.8 7.8 6.2 6.2"/></svg>'
)

APPROACHES = {
    "consensus": {
        "label": "Learning by Consensus",
        "icon": ICON_USERS,
        "description": "Each client learns locally and predictions are combined by majority vote.",
        "chip": "Independent learning",
        "available": True,
    },
    "collaboration": {
        "label": "Learning by Collaboration",
        "icon": ICON_LINK,
        "description": "Joint program search through federated learning.",
        "chip": "Shared model",
        "available": True,
    },
    "coordination": {
        "label": "Learning by Coordination",
        "icon": ICON_GEAR,
        "description": "Clients coordinate the search process to learn a global program.",
        "chip": "Coordinated search",
        "available": True,
    },
}


# ---------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------

st.session_state.setdefault("wizard_step", 1)
st.session_state.setdefault("wizard_method", "consensus")
st.session_state.setdefault("wizard_dataset", "zendo1")
st.session_state.setdefault("wizard_clients", 3)
st.session_state.setdefault("wizard_partition", "iid")
st.session_state.setdefault("wizard_runs", 1)
st.session_state.setdefault("wizard_seed", 42)
st.session_state.setdefault("wizard_learner", "popper")
st.session_state.setdefault("wizard_timeout", 600)
st.session_state.setdefault("wizard_rounds", 35000)
st.session_state.setdefault("wizard_test_ratio", 20)


def go_to_step(step: int) -> None:
    st.session_state["wizard_step"] = step
    st.rerun()


# ---------------------------------------------------------------------
# Page body
# ---------------------------------------------------------------------

inject_style()

st.markdown('<div class="breadcrumb">Home &gt; Simulation</div>', unsafe_allow_html=True)

header_left, header_right = st.columns([4, 1])

with header_left:
    st.title("Simulation")
    st.caption("Configure and launch a new experiment")

with header_right:
    st.write("")
    if st.button("← Back to experiments", use_container_width=True):
        st.session_state["wizard_step"] = 1
        st.switch_page("app_pages/05_Experiments.py")

render_step_indicator(st.session_state["wizard_step"])
st.divider()

current_step = st.session_state["wizard_step"]


# =======================================================================
# STEP 1 — Method
# =======================================================================

ACCENT_STYLE = {
    "consensus": (PALETTE["primary"], PALETTE["primary_soft"]),
    "collaboration": (PALETTE["primary"], PALETTE["primary_soft"]),
    "coordination": (PALETTE["primary"], PALETTE["primary_soft"]),
}

if current_step == 1:
    st.markdown("### 1. Choose a learning approach")
    st.write("")

    method_columns = st.columns(3)

    for column, (key, approach) in zip(method_columns, APPROACHES.items()):
        with column:
            is_selected = st.session_state["wizard_method"] == key
            accent, accent_soft = ACCENT_STYLE.get(key, (PALETTE["primary"], PALETTE["primary_soft"]))

            border_color = accent if is_selected else PALETTE["border"]
            title_color = accent if is_selected else PALETTE["text"]
            chip_bg = accent_soft if is_selected else PALETTE["neutral_soft"]
            chip_color = accent if is_selected else PALETTE["text_muted"]
            badge_html = (
                f'<div style="position:absolute; top:14px; right:14px; width:26px; '
                f'height:26px; border-radius:50%; background:{accent}; color:#fff; '
                f'display:flex; align-items:center; justify-content:center; '
                f'font-size:0.8rem; font-weight:700; z-index:3;">✓</div>'
                if is_selected
                else ""
            )

            st.markdown(
                f'<div style="position:relative; border:2px solid {border_color}; '
                f'border-radius:16px; background:#FFFFFF; padding:20px 18px 16px 18px; '
                f'margin-bottom:10px;">'
                f"{badge_html}"
                f'<div style="display:flex; justify-content:center;">{approach["icon"]}</div>'
                f'<div style="font-size:1.12rem; font-weight:700; color:{title_color}; '
                f'margin:10px 0 6px 0;">{approach["label"]}</div>'
                f'<div style="font-size:0.85rem; color:{PALETTE["text_muted"]}; '
                f'min-height:55px; margin-bottom:10px;">{approach["description"]}</div>'
                f'<span class="badge" style="color:{chip_color}; background:{chip_bg};">'
                f'{approach["chip"]}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

            clicked = st.button(
                "Selected ✓" if is_selected else "Select this approach",
                key=f"select_{key}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            )

            if clicked:
                st.session_state["wizard_method"] = key
                st.rerun()

    st.write("")
    _, continue_col = st.columns([4, 1])
    with continue_col:
        if st.button("Continue →", type="primary", use_container_width=True):
            go_to_step(2)


# =======================================================================
# STEP 2 — Parameters
# =======================================================================

elif current_step == 2:
    method = st.session_state["wizard_method"]
    approach = APPROACHES[method]
    is_consensus = method == "consensus"

    st.markdown(f"### Simulation — {approach['label'].replace('Learning by ', '')}")
    st.caption("Configure the parameters for your experiment")
    st.write("")

    settings_left, settings_right = st.columns(2)

    with settings_left:
        with st.container(border=True):
            st.markdown('<div class="section-title">Dataset and learner</div>', unsafe_allow_html=True)

            available_datasets = get_available_datasets() or ["zendo1"]
            current_dataset = st.session_state["wizard_dataset"]
            if current_dataset not in available_datasets:
                current_dataset = available_datasets[0]

            st.session_state["wizard_dataset"] = st.selectbox(
                "Dataset",
                options=available_datasets,
                index=available_datasets.index(current_dataset),
                help="The logical dataset (examples + background knowledge) the clients will learn from.",
            )
            st.caption(
                "Visual concept learning dataset"
                if st.session_state["wizard_dataset"].startswith("zendo")
                else "Relational learning dataset"
            )

            if is_consensus:
                learner_options = ["popper", "andante"]
                st.session_state["wizard_learner"] = st.selectbox(
                    "Learner",
                    options=learner_options,
                    format_func=lambda key: "Popper" if key == "popper" else "Andante",
                    index=learner_options.index(st.session_state["wizard_learner"]),
                    help="The ILP engine each client uses to learn its own local hypothesis.",
                )
                st.caption("ILP learner")
            else:
                st.session_state["wizard_learner"] = "popper"
                st.text_input("Learner", value="Popper", disabled=True)
                st.caption("Federated search always uses Popper's generate-test-constrain loop.")

    with settings_right:
        with st.container(border=True):
            st.markdown('<div class="section-title">Experiment settings</div>', unsafe_allow_html=True)

            clients_col, partition_col = st.columns(2)

            with clients_col:
                st.session_state["wizard_clients"] = st.selectbox(
                    "Number of clients",
                    options=[2, 3, 10],
                    index=[2, 3, 10].index(st.session_state["wizard_clients"]),
                )

            with partition_col:
                st.markdown("Partition strategy")
                partition_choice = st.radio(
                    "Partition strategy",
                    options=["iid", "non_iid"],
                    format_func=lambda key: "IID" if key == "iid" else "Non-IID",
                    index=["iid", "non_iid"].index(st.session_state["wizard_partition"]),
                    horizontal=True,
                    label_visibility="collapsed",
                )
                st.session_state["wizard_partition"] = partition_choice

            if is_consensus:
                st.write("")
                st.markdown("Train / test split")
                st.session_state["wizard_test_ratio"] = st.slider(
                    "Train / test split",
                    min_value=10,
                    max_value=40,
                    value=st.session_state["wizard_test_ratio"],
                    step=5,
                    format="%d%%",
                    label_visibility="collapsed",
                    help="Percentage of examples held out for the shared test set.",
                )
                st.caption(
                    f"{100 - st.session_state['wizard_test_ratio']}% train / "
                    f"{st.session_state['wizard_test_ratio']}% test"
                )

            st.write("")
            runs_col, seed_col = st.columns(2)

            with runs_col:
                st.session_state["wizard_runs"] = st.number_input(
                    "Number of runs",
                    min_value=1,
                    max_value=20,
                    value=st.session_state["wizard_runs"],
                    step=1,
                )

            with seed_col:
                st.session_state["wizard_seed"] = st.number_input(
                    "Random seed",
                    min_value=0,
                    value=st.session_state["wizard_seed"],
                    step=1,
                )

            if is_consensus:
                st.session_state["wizard_timeout"] = st.number_input(
                    "Local learner timeout (seconds)",
                    min_value=10,
                    value=st.session_state["wizard_timeout"],
                    step=30,
                    help="Safety cap on how long each client's local learner is allowed to run.",
                )
            else:
                st.session_state["wizard_rounds"] = st.number_input(
                    "Maximum rounds",
                    min_value=1,
                    value=st.session_state["wizard_rounds"],
                    step=100,
                    help="Safety cap on federated learning rounds before the run stops.",
                )

    st.write("")
    back_col, continue_col = st.columns([1, 1])
    with back_col:
        if st.button("← Back", use_container_width=True):
            go_to_step(1)
    with continue_col:
        if st.button("Continue →", type="primary", use_container_width=True):
            go_to_step(3)


# =======================================================================
# STEP 3 — Review
# =======================================================================

elif current_step == 3:
    method = st.session_state["wizard_method"]
    approach = APPROACHES[method]
    is_consensus = method == "consensus"

    st.markdown("### Review your experiment")
    st.caption("Double-check the configuration before launching")
    st.write("")

    with st.container(border=True):
        st.markdown(render_badge(approach["label"], "primary"), unsafe_allow_html=True)
        st.write("")

        review_chips = [
            ("Dataset", st.session_state["wizard_dataset"]),
            ("Clients", str(st.session_state["wizard_clients"])),
            ("Partition", st.session_state["wizard_partition"].upper()),
            ("Runs", str(st.session_state["wizard_runs"])),
            ("Seed", str(st.session_state["wizard_seed"])),
        ]

        if is_consensus:
            review_chips.append(("Learner", st.session_state["wizard_learner"].title()))
            review_chips.append(("Timeout", f"{st.session_state['wizard_timeout']} s"))
            review_chips.append(("Test split", f"{st.session_state['wizard_test_ratio']}%"))
        else:
            review_chips.append(("Max rounds", str(st.session_state["wizard_rounds"])))

        render_chips(review_chips)

        default_name = (
            f"{st.session_state['wizard_dataset']}_{method}"
            f"_k{st.session_state['wizard_clients']}_{st.session_state['wizard_partition']}"
        )
        benchmark_name = st.text_input("Experiment name", value=st.session_state.get("wizard_name", default_name))
        st.session_state["wizard_name"] = benchmark_name

        if is_consensus:
            st.caption(
                f"You are about to run **{st.session_state['wizard_runs']}** run(s) on "
                f"**{st.session_state['wizard_dataset']}**, split "
                f"**{st.session_state['wizard_partition'].upper()}** across "
                f"**{st.session_state['wizard_clients']}** clients, each learning locally "
                f"with **{st.session_state['wizard_learner'].title()}**."
            )
        else:
            st.caption(
                f"You are about to run **{st.session_state['wizard_runs']}** run(s) on "
                f"**{st.session_state['wizard_dataset']}**, split "
                f"**{st.session_state['wizard_partition'].upper()}** across "
                f"**{st.session_state['wizard_clients']}** clients."
            )

    st.write("")
    back_col, continue_col = st.columns([1, 1])
    with back_col:
        if st.button("← Back", use_container_width=True):
            go_to_step(2)
    with continue_col:
        if st.button("Launch experiment", type="primary", use_container_width=True):
            go_to_step(4)


# =======================================================================
# STEP 4 — Run
# =======================================================================

elif current_step == 4:
    method = st.session_state["wizard_method"]
    is_consensus = method == "consensus"

    st.markdown("### Running your experiment")
    st.write("")

    if not st.session_state.get("_wizard_launched"):
        config = BenchmarkConfig(
            name=st.session_state["wizard_name"].strip(),
            approach=method,
            dataset=st.session_state["wizard_dataset"],
            number_of_clients=int(st.session_state["wizard_clients"]),
            partition_strategy=st.session_state["wizard_partition"],
            number_of_runs=int(st.session_state["wizard_runs"]),
            base_seed=int(st.session_state["wizard_seed"]),
            learner=st.session_state["wizard_learner"],
            rounds=int(st.session_state["wizard_rounds"]),
            timeout=int(st.session_state["wizard_timeout"]),
            server_address="localhost:8080",
        )

        try:
            with st.status("Running experiment…", expanded=True) as status:
                chips = [
                    ("Dataset", st.session_state["wizard_dataset"]),
                    ("Clients", str(st.session_state["wizard_clients"])),
                    ("Partition", st.session_state["wizard_partition"]),
                    ("Runs", str(st.session_state["wizard_runs"])),
                ]
                if is_consensus:
                    chips.append(("Learner", st.session_state["wizard_learner"].title()))
                else:
                    chips.append(("Max rounds", str(st.session_state["wizard_rounds"])))
                render_chips(chips)

                launcher = BenchmarkLauncher()
                benchmark_id = launcher.run(config)

                st.session_state["_wizard_launched"] = True
                st.session_state["_wizard_benchmark_id"] = benchmark_id

                status.update(
                    label=f"Experiment #{benchmark_id} completed",
                    state="complete",
                    expanded=False,
                )

            st.rerun()

        except Exception as error:
            st.error(f"Experiment failed: {error}")
            if st.button("← Back to parameters"):
                st.session_state["wizard_step"] = 2
                st.rerun()

    else:
        benchmark_id = st.session_state["_wizard_benchmark_id"]
        st.success(f"Experiment #{benchmark_id} completed successfully.")
        st.write("")

        view_col, new_col = st.columns(2)
        with view_col:
            if st.button("View results →", type="primary", use_container_width=True):
                st.session_state["selected_benchmark_id"] = benchmark_id
                st.session_state["experiments_view"] = "detail"
                for key in [
                    "wizard_step",
                    "_wizard_launched",
                    "_wizard_benchmark_id",
                    "wizard_name",
                ]:
                    st.session_state.pop(key, None)
                st.switch_page("app_pages/05_Experiments.py")
        with new_col:
            if st.button("Launch another experiment", use_container_width=True):
                for key in ["_wizard_launched", "_wizard_benchmark_id", "wizard_name"]:
                    st.session_state.pop(key, None)
                st.session_state["wizard_step"] = 1
                st.rerun()

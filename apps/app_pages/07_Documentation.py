from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="Documentation | FILP",
    page_icon=":material/menu_book:",
    layout="wide",
)

if hasattr(st, "logo"):
    try:
        st.logo(str(PROJECT_ROOT / "assets" / "filp_wordmark_white.svg"), size="large")
    except Exception:
        pass


PALETTE = {
    "bg_card": "#F6F8FC",
    "border": "#E2E8F5",
    "text_muted": "#5B6472",
    "text": "#1F2430",
    "primary": "#3E63DE",
    "primary_soft": "#EAF0FE",
    "neutral_soft": "#EEF1F6",
}

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

    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {PALETTE["primary"]} !important;
    }}
    div[data-baseweb="tab-highlight"] {{
        background-color: {PALETTE["primary"]} !important;
    }}
    div[data-baseweb="tab-border"] {{
        background-color: {PALETTE["border"]} !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 14px !important;
    }}

    .section-title {{
        font-size: 1.15rem;
        font-weight: 700;
        color: {PALETTE["text"]};
        margin: 0 0 4px 0;
    }}
    .section-caption {{
        font-size: 0.9rem;
        color: {PALETTE["text_muted"]};
        margin-bottom: 12px;
    }}

    .info-card {{
        height: 100%;
        padding: 1.1rem 1.2rem;
        border-radius: 14px;
        background: {PALETTE["bg_card"]};
        border: 1px solid {PALETTE["border"]};
    }}
    .info-card .info-title {{
        font-weight: 700;
        color: {PALETTE["text"]};
        margin-bottom: 4px;
    }}
    .info-card .info-body {{
        color: {PALETTE["text_muted"]};
        font-size: 0.9rem;
        line-height: 1.5;
    }}

    .step-card {{
        height: 100%;
        padding: 1.1rem 1.2rem;
        border-radius: 14px;
        background: {PALETTE["primary_soft"]};
        border: 1px solid {PALETTE["border"]};
        margin-bottom: 18px;
    }}
    .step-card .step-number {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: 999px;
        background: {PALETTE["primary"]};
        color: white;
        font-size: 0.8rem;
        font-weight: 700;
        margin-bottom: 8px;
    }}
    .step-card .step-title {{
        font-weight: 700;
        color: {PALETTE["text"]};
        margin-bottom: 4px;
    }}
    .step-card .step-body {{
        color: {PALETTE["text_muted"]};
        font-size: 0.88rem;
        line-height: 1.5;
    }}

    .glossary-card {{
        padding: 1.2rem 1.4rem;
        border-radius: 14px;
        background: {PALETTE["bg_card"]};
        border: 1px solid {PALETTE["border"]};
    }}
    .glossary-card dt {{
        font-weight: 700;
        color: {PALETTE["text"]};
        margin-top: 10px;
    }}
    .glossary-card dt:first-child {{ margin-top: 0; }}
    .glossary-card dd {{
        color: {PALETTE["text_muted"]};
        font-size: 0.9rem;
        margin: 2px 0 0 0;
        line-height: 1.5;
    }}

    .faq-card {{
        padding: 1.1rem 1.3rem;
        border-radius: 14px;
        background: #FFFFFF;
        border: 1px solid {PALETTE["border"]};
        margin-bottom: 14px;
    }}
    .faq-card .faq-q {{
        font-weight: 700;
        color: {PALETTE["text"]};
        margin-bottom: 4px;
    }}
    .faq-card .faq-a {{
        color: {PALETTE["text_muted"]};
        font-size: 0.9rem;
        line-height: 1.55;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def render_step_card(number: int, title: str, body: str) -> None:
    st.markdown(
        f'<div class="step-card"><div class="step-number">{number}</div>'
        f'<div class="step-title">{title}</div><div class="step-body">{body}</div></div>',
        unsafe_allow_html=True,
    )


def render_info_card(title: str, body: str) -> None:
    st.markdown(
        f'<div class="info-card"><div class="info-title">{title}</div>'
        f'<div class="info-body">{body}</div></div>',
        unsafe_allow_html=True,
    )


def render_faq(question: str, answer: str) -> None:
    st.markdown(
        f'<div class="faq-card"><div class="faq-q">{question}</div>'
        f'<div class="faq-a">{answer}</div></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Page introduction
# ---------------------------------------------------------------------

st.title("Documentation")
st.caption("Guides and reference material for the FILP platform.")

st.write("")

getting_started_tab, concepts_tab, datasets_tab, results_tab, faq_tab = st.tabs(
    ["Getting started", "Concepts", "Datasets", "Reading results", "FAQ"]
)


# ===================================================================
# GETTING STARTED
# ===================================================================

with getting_started_tab:
    st.markdown('<div class="section-title">Run your first experiment</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">Four steps from the Simulation wizard to a learned hypothesis</div>',
        unsafe_allow_html=True,
    )

    step_1, step_2, step_3, step_4 = st.columns(4)
    with step_1:
        render_step_card(1, "Choose an approach", "Pick Learning by Collaboration, Coordination or Consensus.")
    with step_2:
        render_step_card(2, "Configure", "Select a dataset, the number of clients, the partitioning strategy and any hyperparameters.")
    with step_3:
        render_step_card(3, "Launch", "The platform runs the federated ILP loop across simulated clients.")
    with step_4:
        render_step_card(4, "Review results", "Inspect the learned hypothesis and metrics from the Experiments page.")

    st.write("")
    st.page_link("app_pages/04_Simulation.py", label="Open Simulation")

    st.divider()

    st.markdown('<div class="section-title">Quick glossary</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="glossary-card">
        <dl>
        <dt>Hypothesis</dt>
        <dd>A logic program — a set of Prolog rules — learned from examples that covers the positive examples and excludes the negative ones.</dd>
        <dt>Background knowledge (BK)</dt>
        <dd>Facts and auxiliary predicates available to the learner in addition to the examples themselves.</dd>
        <dt>Bias</dt>
        <dd>The declarative constraints on what a hypothesis may look like — which predicates, types and directions are allowed (Popper's <code>bias.pl</code>, or Progol/Aleph mode declarations).</dd>
        <dt>Client</dt>
        <dd>A simulated participant holding one local partition of the dataset. Clients never share their raw examples with each other or the server.</dd>
        <dt>Round</dt>
        <dd>One iteration of the federated protocol — a hypothesis (or step of the search) is distributed, evaluated locally, and feedback is aggregated.</dd>
        <dt>Consensus vote</dt>
        <dd>In Learning by Consensus, the majority vote across each client's independently learned hypothesis that produces the final prediction for a test example.</dd>
        </dl>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===================================================================
# CONCEPTS
# ===================================================================

with concepts_tab:
    st.markdown('<div class="section-title">Where to learn the theory</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">The core concepts are explained in full on two dedicated pages — this is just a map to get you there</div>',
        unsafe_allow_html=True,
    )

    concept_col_1, concept_col_2 = st.columns(2)
    with concept_col_1:
        render_info_card(
            "Inductive Logic Programming",
            "What a logic program is, how Popper searches for one, and how "
            "Progol/Aleph mode declarations relate to a Popper bias. "
            "Includes a full dataset explorer (examples, background "
            "knowledge, bias) for every dataset on the platform.",
        )
        st.write("")
        st.page_link("app_pages/02_Inductive_logic_programming.py", label="Open Inductive logic programming")

    with concept_col_2:
        render_info_card(
            "FILP approaches",
            "The three federated ILP strategies side by side — Learning by "
            "Collaboration (FedPopper), Learning by Coordination "
            "(Bach4Popper) and Learning by Consensus — with their "
            "architecture, aggregation mechanism and related publications.",
        )
        st.write("")
        st.page_link("app_pages/03_FILP_approaches.py", label="Open FILP approaches")

    st.write("")
    st.page_link("app_pages/01_Federated_Learning.py", label="Open Federated Learning overview")


# ===================================================================
# DATASETS
# ===================================================================

with datasets_tab:
    st.markdown('<div class="section-title">Dataset file format</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">Every dataset on the platform follows the same three-file Popper convention</div>',
        unsafe_allow_html=True,
    )

    file_col_1, file_col_2, file_col_3 = st.columns(3)
    with file_col_1:
        render_info_card(
            "<code>exs.pl</code>",
            "The labelled examples — positive facts wrapped in "
            "<code>pos(...)</code> and negative ones in "
            "<code>neg(...)</code>.",
        )
    with file_col_2:
        render_info_card(
            "<code>bk.pl</code>",
            "The background knowledge — facts and helper predicates the "
            "learner can use, shared across every example.",
        )
    with file_col_3:
        render_info_card(
            "<code>bias.pl</code>",
            "The language bias — which head/body predicates, types and "
            "argument directions a hypothesis is allowed to use.",
        )

    st.write("")
    st.markdown(
        "For a federated run, only the training partition is split across "
        "clients — the dataset itself is never duplicated or centralised."
    )
    st.page_link("app_pages/02_Inductive_logic_programming.py", label="Browse datasets")


# ===================================================================
# READING RESULTS
# ===================================================================

with results_tab:
    st.markdown('<div class="section-title">Metrics</div>', unsafe_allow_html=True)

    metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)
    with metric_col_1:
        render_info_card("Accuracy", "Share of test examples correctly classified, positive or negative.")
    with metric_col_2:
        render_info_card("Precision", "Of the examples predicted positive, the fraction that truly are.")
    with metric_col_3:
        render_info_card("Recall", "Of the truly positive examples, the fraction correctly identified.")
    with metric_col_4:
        render_info_card("F1", "The harmonic mean of precision and recall.")

    st.divider()

    st.markdown('<div class="section-title">Reading a consensus decision</div>', unsafe_allow_html=True)
    st.markdown(
        "For Learning by Consensus, the platform reports the vote produced "
        "by every learned hypothesis for each test example, not just the "
        "final prediction:"
    )

    with st.container(border=True):
        st.code(
            "Example 28\n\n"
            "True label: NEG\n\n"
            "H1 → NEG\n"
            "H2 → POS\n"
            "H3 → NEG\n\n"
            "Positive votes:      1 / 3\n"
            "Required majority:   2\n\n"
            "Consensus: NEG ✓",
            language=None,
        )
    st.caption(
        "A ratio such as 1/3 or 2/3 here reflects the level of agreement "
        "between independently learned hypotheses — it is not a predictive "
        "probability."
    )

    st.write("")
    st.page_link("app_pages/05_Experiments.py", label="Open Experiments")


# ===================================================================
# FAQ
# ===================================================================

with faq_tab:
    st.markdown('<div class="section-title">Frequently asked questions</div>', unsafe_allow_html=True)
    st.write("")

    render_faq(
        "I edited a backend file (core/*.py, database/*.py) and now get an "
        "unexpected error — what happened?",
        "Streamlit only re-executes the page script on each rerun; it does "
        "not re-import backend modules that were already loaded in the "
        "running process. After editing a backend file, stop the server "
        "(Ctrl+C) and run <code>streamlit run</code> again so the change "
        "is picked up.",
    )
    render_faq(
        "What's the difference between the three approaches?",
        "Learning by Collaboration and Coordination both search for a "
        "single global hypothesis, federating Popper's search loop through "
        "either direct client-server messages or Bach's tuple-space "
        "coordination. Learning by Consensus instead lets each client "
        "learn its own local hypothesis, and combines them only at "
        "prediction time through majority voting — see the FILP "
        "approaches page for the full comparison.",
    )
    render_faq(
        "Where is my experiment history stored?",
        "Every experiment, benchmark run and result is persisted in the "
        "platform's local SQLite database, so past runs remain browsable "
        "from the Experiments page after a restart.",
    )

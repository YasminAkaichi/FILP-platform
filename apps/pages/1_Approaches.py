from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------
# Project setup
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LINKEDIN_URL = "https://www.linkedin.com/in/yasmine-akaichi-761975197/"


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="FILP Approaches",
    page_icon="",
    layout="wide",
)

# Same fixed sidebar branding slot as every other page.
if hasattr(st, "logo"):
    try:
        st.logo(str(ASSETS / "filp_logo.svg"), size="large")
    except Exception:
        pass


# ---------------------------------------------------------------------
# Visual design system — same accent family as Home / Experiments /
# Datasets, so the whole site reads as one coherent product.
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
    "warning": "#C98A1F",
    "warning_soft": "#FCF1DE",
    "neutral": "#8A93A3",
    "neutral_soft": "#EEF1F6",
}


def inject_style() -> None:
    # Every hand-written HTML snippet below is a single line with no
    # leading indentation — a blank line followed by 4+ spaces of
    # indentation is read as a code block by Streamlit's markdown
    # renderer, which silently breaks custom HTML cards otherwise.
    st.markdown(
        f"""
        <style>
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 4rem;
            max-width: 1300px;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 14px !important;
        }}

        div.stButton > button[kind="primary"] {{
            background-color: {PALETTE["primary"]};
            border-color: {PALETTE["primary"]};
        }}
        div.stButton > button[kind="primary"]:hover {{
            background-color: #4A6BC4;
            border-color: #4A6BC4;
        }}

        .approach-hero {{
            padding: 1.8rem 2rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #EAF0FE 0%, #F6F8FC 100%);
            border: 1px solid {PALETTE["border"]};
            margin-bottom: 1.4rem;
        }}
        .approach-hero p {{
            color: {PALETTE["text_muted"]};
            font-size: 1.02rem;
            line-height: 1.6;
            max-width: 820px;
            margin: 8px 0 0 0;
        }}

        .section-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: {PALETTE["text"]};
            margin: 0 0 4px 0;
        }}
        .section-caption {{
            font-size: 0.92rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 12px;
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
        }}

        .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 4px 0; }}
        .chip {{ border-radius: 999px; padding: 5px 13px; font-size: 0.83rem; font-weight: 600; }}
        .chip-primary {{ background: {PALETTE["primary_soft"]}; color: {PALETTE["primary"]}; }}
        .chip-neutral {{ background: {PALETTE["neutral_soft"]}; color: {PALETTE["text"]}; }}

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
        .step-arrow {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            font-size: 1.4rem;
            color: {PALETTE["primary"]};
        }}

        .role-card {{
            padding: 1.3rem 1.4rem;
            border-radius: 16px;
            background: {PALETTE["bg_card"]};
            border: 1px solid {PALETTE["border"]};
        }}
        .role-card h4 {{ margin: 6px 0 10px 0; color: {PALETTE["text"]}; }}
        .role-card ul {{ margin: 0; padding-left: 1.1rem; color: {PALETTE["text_muted"]}; font-size: 0.92rem; line-height: 1.7; }}

        .feature-card {{
            height: 100%;
            padding: 1rem 1.15rem;
            border-radius: 14px;
            background: white;
            border: 1px solid {PALETTE["border"]};
            border-left: 4px solid {PALETTE["primary"]};
            margin-bottom: 18px;
        }}
        .feature-card .feature-title {{ font-weight: 700; color: {PALETTE["text"]}; margin-bottom: 3px; }}
        .feature-card .feature-body {{ color: {PALETTE["text_muted"]}; font-size: 0.88rem; line-height: 1.5; }}

        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin: 4px 0; }}
        .metric-card {{ background: {PALETTE["bg_card"]}; border: 1px solid {PALETTE["border"]}; border-radius: 12px; padding: 14px 16px; }}
        .metric-card .metric-label {{ font-size: 0.78rem; color: {PALETTE["text_muted"]}; font-weight: 500; margin-bottom: 4px; }}
        .metric-card .metric-value {{ font-size: 1.2rem; color: {PALETTE["text"]}; font-weight: 700; line-height: 1.2; }}

        .coming-soon-card {{
            padding: 2.4rem 2.6rem;
            border-radius: 18px;
            background: {PALETTE["neutral_soft"]};
            border: 1px dashed {PALETTE["border"]};
            text-align: center;
            max-width: 760px;
            margin: 1.5rem auto;
        }}
        .coming-soon-card .badge {{ margin-bottom: 10px; }}
        .coming-soon-card h3 {{ margin: 0 0 8px 0; color: {PALETTE["text"]}; }}
        .coming-soon-card p {{ color: {PALETTE["text_muted"]}; line-height: 1.6; margin-bottom: 0; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_badge(text: str, kind: str = "success") -> str:
    styles = {
        "success": (PALETTE["success"], PALETTE["success_soft"]),
        "warning": (PALETTE["warning"], PALETTE["warning_soft"]),
        "neutral": (PALETTE["neutral"], PALETTE["neutral_soft"]),
    }
    color, bg = styles.get(kind, styles["neutral"])
    return f'<span class="badge" style="color:{color};background:{bg};">{text}</span>'


def render_chips(labels: list[str]) -> None:
    chips = "".join(f'<span class="chip chip-primary">{label}</span>' for label in labels)
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)


def render_info_card(title: str, body: str) -> None:
    st.markdown(
        f'<div class="info-card"><div class="info-title">{title}</div>'
        f'<div class="info-body">{body}</div></div>',
        unsafe_allow_html=True,
    )


def render_step_card(number: int, title: str, body: str) -> None:
    st.markdown(
        f'<div class="step-card"><div class="step-number">{number}</div>'
        f'<div class="step-title">{title}</div><div class="step-body">{body}</div></div>',
        unsafe_allow_html=True,
    )


def render_feature_card(icon: str, title: str, body: str) -> None:
    st.markdown(
        f'<div class="feature-card"><div class="feature-title">{icon} {title}</div>'
        f'<div class="feature-body">{body}</div></div>',
        unsafe_allow_html=True,
    )


def render_metric_grid(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div></div>'
        for label, value in items
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def render_coming_soon(title: str, body: str) -> None:
    st.markdown(
        '<div class="coming-soon-card">'
        + render_badge("🔜 Planned", "neutral")
        + f"<h3>{title}</h3>"
        + f"<p>{body}</p>"
        + "</div>",
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([2, 2, 2])
    with mid:
        st.link_button("Follow progress on LinkedIn", LINKEDIN_URL, use_container_width=True)


# ---------------------------------------------------------------------
# Page introduction
# ---------------------------------------------------------------------

inject_style()

st.title("FILP Research Approaches")
st.caption(
    "Three complementary approaches to Federated Inductive Logic "
    "Programming, developed as part of my PhD thesis."
)

render_chips(
    [
        " Learning by Collaboration — available",
        " Learning by Coordination — planned",
        " Learning by Consensus — planned",
    ]
)

st.write("")

collaboration_tab, coordination_tab, consensus_tab = st.tabs(
    [
        "  Learning by Collaboration",
        "  Learning by Coordination",
        "  Learning by Consensus",
    ]
)


# ===================================================================
# LEARNING BY COLLABORATION
# ===================================================================

with collaboration_tab:

    # ---------------------------------------------------------------
    # Intro / hero
    # ---------------------------------------------------------------

    st.markdown(
        '<div class="approach-hero">'
        + render_badge(" Available now", "success")
        + '<div class="section-title" style="font-size:1.6rem; margin-top:10px;">Learning by Collaboration</div>'
        + "<p>Federated symbolic learning without sharing raw examples. Several "
        "clients collaboratively learn an interpretable logic program while "
        "keeping their local examples private: a central Popper server "
        "generates candidate hypotheses, each client evaluates them against "
        "its local data, and returns symbolic feedback rather than raw "
        "examples or numerical gradients.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    render_chips(["🌸 Flower", "🧠 Popper", "📚 Inductive Logic Programming", "🌍 Federated Learning", "✨ Symbolic AI"])

    st.write("")

    cta_left, cta_right, _spacer = st.columns([2, 2, 3])
    with cta_left:
        st.page_link(
            "pages/3_Experiments.py",
            label="🧪 Try it on the Experiments page",
            use_container_width=True,
        )
    with cta_right:
        st.page_link(
            "pages/2_Datasets.py",
            label="📚 Explore the datasets first",
            use_container_width=True,
        )

    st.divider()

    # ---------------------------------------------------------------
    # Overview
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">How the server and the clients split the work</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        collaboration_figure = ASSETS / "collaboration.png"

        figure_left, figure_center, figure_right = st.columns([1, 3, 1])

        with figure_center:
            if collaboration_figure.is_file():
                st.image(
                    str(collaboration_figure),
                    caption="Learning by Collaboration architecture",
                    use_container_width=True,
                )
            else:
                st.warning(
                    f"Collaboration figure not found.\n\nExpected path: `{collaboration_figure}`"
                )

        st.write(
            "The federated server manages the symbolic search: it generates a "
            "candidate hypothesis, broadcasts it to the clients, aggregates the "
            "returned outcomes and constructs new constraints. The clients only "
            "perform local testing, their examples and background knowledge "
            "remain local. The information exchanged is symbolic: outcomes, "
            "scores, confusion-matrix values and clause-level feedback, never "
            "raw data."
        )

    st.divider()

    # ---------------------------------------------------------------
    # Protocol
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">Protocol</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">One round of the collaboration loop, step by step</div>',
        unsafe_allow_html=True,
    )

    protocol_steps = [
        ("Generate", "The server uses Popper to generate a candidate hypothesis from the current hypothesis space."),
        ("Broadcast", "The candidate hypothesis is sent to every participating client."),
        ("Evaluate", "Each client evaluates the hypothesis against its local examples."),
        ("Return feedback", "Clients return ε outcomes, score, TP, FN, TN, FP and clause-level feedback."),
        ("Aggregate", "The server combines client outcomes into a global symbolic decision."),
        ("Constrain", "New constraints are generated before Popper searches for the next hypothesis."),
    ]

    row_1, row_2 = st.columns(3, gap="large"), st.columns(3, gap="large")

    row_a, row_b = st.columns(3, gap="large"), st.columns(3, gap="large")

    for column, (index, (title, body)) in zip(row_1, enumerate(protocol_steps[:3], start=1)):
        with column:
            render_step_card(index, title, body)

    for column, (index, (title, body)) in zip(row_2, enumerate(protocol_steps[3:], start=4)):
        with column:
            render_step_card(index, title, body)

    st.caption("Steps 1–6 repeat every round until Popper converges on a valid hypothesis or the round cap is reached.")

    st.divider()

    # ---------------------------------------------------------------
    # Architecture
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">Architecture</div>', unsafe_allow_html=True)

    server_column, client_column = st.columns(2)

    with server_column:
        st.markdown(
            '<div class="role-card">'
            + render_badge("Server-side", "neutral")
            + "<h4>Federated server</h4>"
            + "<ul>"
            "<li>Candidate hypothesis generation</li>"
            "<li>FedPopper strategy</li>"
            "<li>Outcome aggregation</li>"
            "<li>Score aggregation</li>"
            "<li>Clause-feedback aggregation</li>"
            "<li>Constraint generation</li>"
            "<li>Best-program tracking</li>"
            "</ul></div>",
            unsafe_allow_html=True,
        )

    with client_column:
        st.markdown(
            '<div class="role-card">'
            + render_badge("Client-side", "neutral")
            + "<h4>Distributed clients</h4>"
            + "<ul>"
            "<li>Local dataset partition</li>"
            "<li>Local background knowledge</li>"
            "<li>Local Popper tester</li>"
            "<li>TP, FN, TN and FP computation</li>"
            "<li>Epsilon-positive outcome</li>"
            "<li>Epsilon-negative outcome</li>"
            "<li>Clause inconsistency testing</li>"
            "<li>Clause total-incompleteness testing</li>"
            "</ul></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ---------------------------------------------------------------
    # Information exchanged
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">Information exchanged</div>', unsafe_allow_html=True)

    server_to_client, client_to_server = st.columns(2)

    with server_to_client:
        st.markdown("**Server → Clients**")
        st.table(
            {
                "Information": ["Candidate hypothesis", "Current round"],
                "Purpose": ["Local symbolic evaluation", "Execution tracking"],
            }
        )

    with client_to_server:
        st.markdown("**Clients → Server**")
        st.table(
            {
                "Information": [
                    "ε+",
                    "ε−",
                    "Local score",
                    "TP / FN / TN / FP",
                    "Inconsistent clauses",
                    "Totally incomplete clauses",
                ],
                "Purpose": [
                    "Completeness feedback",
                    "Consistency feedback",
                    "Hypothesis quality",
                    "Detailed local evaluation",
                    "Generalisation constraints",
                    "Redundancy constraints",
                ],
            }
        )

    st.divider()

    # ---------------------------------------------------------------
    # Key characteristics
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">Key characteristics</div>', unsafe_allow_html=True)

    characteristics = [
        ("🔒", "Privacy-preserving", "Raw examples and local background knowledge remain on the clients."),
        ("🧾", "Interpretable", "The learned model is an explicit logic program rather than a black-box numerical model."),
        ("🤝", "Symbolic collaboration", "Clients return symbolic evaluation feedback instead of model parameters or raw data."),
        ("⚙️", "Configurable", "Experiments support a variable number of clients and IID or Non-IID data distributions."),
        ("🧭", "Constraint-driven", "Aggregated client feedback is transformed into constraints that guide the Popper search."),
        ("📊", "Reproducible", "Experiment configurations, partitions, rules and execution results are recorded by the FILP Platform."),
    ]

    row_a, row_b = st.columns(3), st.columns(3)

    for column, item in zip(row_a, characteristics[:3]):
        with column:
            render_feature_card(*item)

    for column, item in zip(row_b, characteristics[3:]):
        with column:
            render_feature_card(*item)

    st.write("")

    with st.expander("Technical details: clause-level feedback"):
        st.markdown(
            "Clause-level inconsistency and total-incompleteness checks are "
            "performed locally because they depend on private client data."
        )
        st.code(
            "global_inconsistent(rule) = any(\n"
            "    client.is_inconsistent(rule)\n"
            "    for client in clients\n"
            ")\n\n"
            "global_totally_incomplete(rule) = all(\n"
            "    client.is_totally_incomplete(rule)\n"
            "    for client in clients\n"
            ")",
            language="python",
        )

    st.divider()

    # ---------------------------------------------------------------
    # Example output
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">Example learned rule</div>', unsafe_allow_html=True)
    st.code(
        "zendo(A):- size(C,D), contact(B,C), piece(A,B), red(B), small(D).",
        language="prolog",
    )

    st.divider()

    # ---------------------------------------------------------------
    # Experimental capabilities
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">Experimental capabilities</div>', unsafe_allow_html=True)

    render_metric_grid(
        [
            ("Partitioning", "IID / Non-IID"),
            ("Number of clients", "Configurable"),
            ("Datasets", "Multiple"),
            ("Output", "Logic program"),
        ]
    )

    st.caption(
        "Execution time, number of programs, number of rounds, final score "
        "and client-level metrics are loaded live from the FILP experiment "
        "database on the Experiments page."
    )

    st.divider()

    # ---------------------------------------------------------------
    # Implementation
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">Implementation</div>', unsafe_allow_html=True)

    implementation_1, implementation_2, implementation_3 = st.columns(3)

    with implementation_1:
        render_info_card("Learning engine", "Popper generates hypotheses and constraints.")
    with implementation_2:
        render_info_card("Federated infrastructure", "Flower handles communication between the server and clients.")
    with implementation_3:
        render_info_card("Experiment platform", "The FILP launcher manages partitions, processes, artifacts and database persistence.")

    st.divider()

    # ---------------------------------------------------------------
    # Research paper
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">📄 Related publication</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            "**Akaichi, Y., Barkallah, M., Jacquet, J.-M., Linden, I., & Vanhoof, W. (2026).** "
            "[*Bach4Popper: Towards Federated Inductive Logic Programming Using Coordination.*]"
            "(https://link.springer.com/chapter/10.1007/978-3-032-28358-0_7) "
            "In *International Conference on Coordination Models and Languages* (pp. 136–156). Springer, Cham."
        )


# ===================================================================
# LEARNING BY COORDINATION
# ===================================================================

with coordination_tab:
    render_coming_soon(
        "Learning by Coordination",
        "This section will present Bach4Popper, the coordination-space "
        "architecture, the Bach store, the distributed protocol and the "
        "associated experimental results.",
    )


# ===================================================================
# LEARNING BY CONSENSUS
# ===================================================================

with consensus_tab:
    render_coming_soon(
        "Learning by Consensus",
        "This section will present the consensus-based FILP approach, "
        "including the participating ILP learners, the voting or "
        "aggregation mechanism and the associated experimental evaluation.",
    )
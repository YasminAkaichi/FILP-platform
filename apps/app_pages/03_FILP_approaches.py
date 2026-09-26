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
    page_icon=":material/compare_arrows:",
    layout="wide",
)

if hasattr(st, "logo"):
    try:
        st.logo(str(ASSETS / "filp_wordmark_white.svg"), size="large")
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
            padding-top: 3rem;
            padding-bottom: 3rem;
            padding-left: 2.2rem;
            padding-right: 2.2rem;
            max-width: 100% !important;
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

        .breadcrumb {{
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 4px;
        }}

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

st.markdown('<div class="breadcrumb">Home &gt; FILP approaches</div>', unsafe_allow_html=True)

st.title("FILP Research Approaches")
st.caption(
    "Three complementary approaches to Federated Inductive Logic "
    "Programming, developed as part of my PhD thesis."
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
    # Intro / hero (left) + Architecture (right), side by side
    # ---------------------------------------------------------------

    intro_col, arch_col = st.columns([1, 1], gap="large")

    with intro_col:
        st.markdown(
            '<div class="approach-hero" style="height:100%;">'
            + '<div class="section-title" style="font-size:1.6rem; margin-top:10px;">Learning by Collaboration</div>'
            + "<p>FedPopper federates Popper's generate-test-constrain loop: a "
            "central server generates candidate hypotheses and a set of clients "
            "test them against their own local data. Clients never exchange "
            "examples, background knowledge or gradients — only a coarse "
            "symbolic outcome and a score reach the server.</p>"
            "<p>FedPopper is the <b>proof of practicality</b>: it plugs "
            "straight into <b>Flower</b>, the industry-standard federated "
            "learning framework, with a custom strategy that aggregates "
            "symbolic ALL/SOME/NONE outcomes instead of averaging model "
            "weights. The server talks to clients <b>directly</b>, so it "
            "benefits from Flower's mature, production-ready ecosystem.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        render_chips(["Flower", "Popper", "Answer Set Programming", "Federated Learning", "Symbolic AI"])

    with arch_col:
        st.markdown('<div class="section-title">Architecture</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-caption">The server never sees a client\'s data — only hypotheses go out, only outcomes come back</div>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            collaboration_figure = ASSETS / "collaboration.png"

            if collaboration_figure.is_file():
                st.image(
                    str(collaboration_figure),
                    caption="FedPopper architecture (Akaichi et al.)",
                    use_container_width=True,
                )
            else:
                st.warning(
                    f"Collaboration figure not found.\n\nExpected path: `{collaboration_figure}`"
                )

        st.caption(
            "The server holds the language bias and generates each candidate "
            "hypothesis; it never accesses a client's dataset. Each client holds "
            "a local partition (E+, E−, B) and tests the hypothesis locally, "
            "returning only a symbolic outcome (ε+, ε−) and a score s = TP+TN — "
            "never the underlying examples, background knowledge or coverage "
            "counts."
        )

    st.divider()

    # ---------------------------------------------------------------
    # How the aggregation works
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">How the aggregation works</div>', unsafe_allow_html=True)
    st.write(
        "At each round, the server broadcasts a hypothesis and collects one "
        "symbolic outcome per client. Outcomes are combined into a single "
        "global signal: ALL if every client reports ALL, NONE if every "
        "client reports NONE, SOME otherwise. Scores are simply summed. "
        "This aggregation is proven to match what centralized Popper would "
        "compute on the pooled data, so federating the evaluation step does "
        "not change what is learned — only how it is computed."
    )

    step_1, step_2, step_3, step_4 = st.columns(4)
    with step_1:
        render_info_card("Generate", "The server generates a candidate hypothesis from the constraints accumulated so far.")
    with step_2:
        render_info_card("Broadcast", "The hypothesis is sent to every client.")
    with step_3:
        render_info_card("Test", "Each client evaluates it locally and returns only its outcome and score.")
    with step_4:
        render_info_card("Aggregate & constrain", "The server combines the outcomes and derives the next constraint, or stops if the hypothesis is complete and consistent.")

    st.divider()

    # ---------------------------------------------------------------
    # What the paper shows
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">What the paper shows</div>', unsafe_allow_html=True)

    result_1, result_2 = st.columns(2)
    with result_1:
        render_info_card(
            "Correctness",
            "Across all datasets and partitioning strategies tested, "
            "FedPopper reaches the same hypothesis as centralized Popper, "
            "matching it exactly in coverage.",
        )
    with result_2:
        render_info_card(
            "Cost of federation",
            "The coordination overhead of federation is separable from the "
            "symbolic search itself: the number of refinement rounds is "
            "preserved, and the extra cost is purely communication and "
            "synchronization.",
        )

    st.divider()

    # ---------------------------------------------------------------
    # Research paper
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">📄 Related publication</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            "**Akaichi, Y., Jacquet, J.-M., Linden, I., & Vanhoof, W.** "
            "*FedPopper: Federated Learning Logic Programs from Aggregated "
            "Failures.* Manuscript under review."
        )
        st.caption(
            "Code: Akaichi, Y., Jacquet, J.-M. The FedPopper Framework. "
            "https://doi.org/10.5281/zenodo.20659933"
        )


# ===================================================================
# LEARNING BY COORDINATION
# ===================================================================

with coordination_tab:

    # ---------------------------------------------------------------
    # Intro / hero (left) + Architecture (right), side by side
    # ---------------------------------------------------------------

    intro_col, arch_col = st.columns([1, 1], gap="large")

    with intro_col:
        st.markdown(
            '<div class="approach-hero" style="height:100%;">'
            + '<div class="section-title" style="font-size:1.6rem; margin-top:10px;">Learning by Coordination</div>'
            + "<p>Bach4Popper coordinates the federated generate-test-constrain "
            "loop through <b>Bach</b>, a tuple-space coordination language "
            "developed at the Nadi Research Institute (University of Namur), "
            "instead of direct client-server message passing. Participants "
            "read and write to a shared coordination store rather than "
            "exchanging point-to-point requests.</p>"
            "<p>Bach4Popper is the <b>proof of generality</b>: it reaches "
            "the exact same symbolic ALL/SOME/NONE aggregation as FedPopper, "
            "but without depending on any federated learning framework at "
            "all. Because nothing addresses anyone directly, participants "
            "can join or leave without the orchestrator knowing them in "
            "advance — a coordination model better suited to unreliable, "
            "decentralized, real-world deployments than a classic "
            "client-server setup.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        render_chips(["Bach", "Popper", "Tuple-space coordination", "Federated Learning", "Symbolic AI"])

    with arch_col:
        st.markdown('<div class="section-title">Architecture</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-caption">The federated server and the client testers never talk to each other directly — everything goes through the Bach store</div>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            coordination_figure = ASSETS / "bach4popper-finals.png"

            if coordination_figure.is_file():
                st.image(
                    str(coordination_figure),
                    caption="Bach4Popper architecture (Akaichi et al., 2026)",
                    use_container_width=True,
                )
            else:
                st.warning(
                    f"Coordination figure not found.\n\nExpected path: `{coordination_figure}`"
                )

        st.caption(
            "The server never contacts a client directly, and clients never "
            "contact each other. The server tells each candidate hypothesis H "
            "into the store and gets the outcomes back; every client asks the "
            "store for H, tests it against its own local data (D1…Dn), and "
            "tells its outcome back into the store."
        )

    st.divider()

    # ---------------------------------------------------------------
    # Why coordination
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">Why coordination, not just collaboration?</div>', unsafe_allow_html=True)
    st.write(
        "Learning by Collaboration relies on a central server directly "
        "orchestrating each round: it sends a hypothesis, waits for every "
        "client to answer, then moves on. Learning by Coordination "
        "reformulates this exchange through a shared coordination space: "
        "participants publish and retrieve information asynchronously via "
        "the store, which decouples when something is produced from when "
        "it is consumed — a pattern suited to distributed, "
        "loosely-synchronized settings."
    )

    st.divider()

    # ---------------------------------------------------------------
    # How Bach coordinates the search
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">How Bach coordinates the search</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">Bach is a Linda-style dialect: a shared, associative store that processes read from and write to using four primitives</div>',
        unsafe_allow_html=True,
    )

    primitive_1, primitive_2, primitive_3, primitive_4 = st.columns(4)
    with primitive_1:
        render_info_card("tell(t)", "Writes tuple t to the shared store. Always succeeds.")
    with primitive_2:
        render_info_card("get(t)", "Reads and removes t from the store — requires t to be present.")
    with primitive_3:
        render_info_card("ask(t)", "Tests whether t is present, without removing it.")
    with primitive_4:
        render_info_card("nask(t)", "Tests whether t is absent from the store.")

    st.caption(
        "Bach was developed at the Nadi Research Institute (Darquennes, "
        "Jacquet & Linden). Bach4Popper uses it as the coordination layer "
        "between the Popper search and the distributed clients."
    )

    st.divider()

    # ---------------------------------------------------------------
    # What the paper shows
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">What the paper shows</div>', unsafe_allow_html=True)

    result_1, result_2 = st.columns(2)
    with result_1:
        render_info_card(
            "Correctness",
            "Bach4Popper is shown, both theoretically and empirically, to be "
            "correct with respect to the corresponding centralized version "
            "of Popper.",
        )
    with result_2:
        render_info_card(
            "Performance",
            "Experimental results show that computational performance is "
            "preserved when moving from a centralized to a federated "
            "setting.",
        )

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
            "In *International Conference on Coordination Models and Languages* "
            "(COORDINATION 2026), LNCS vol. 16590, pp. 136–156. Springer, Cham."
        )
        st.caption(
            "Code: Akaichi, Y., Jacquet, J.-M. The Bach4Popper Framework. "
            "https://doi.org/10.5281/zenodo.18981901"
        )



# ===================================================================
# LEARNING BY CONSENSUS
# ===================================================================

with consensus_tab:

    # ---------------------------------------------------------------
    # Intro / hero (left) + Architecture (right), side by side
    # ---------------------------------------------------------------

    intro_col, arch_col = st.columns([1, 1], gap="large")

    with intro_col:
        st.markdown(
            '<div class="approach-hero" style="height:100%;">'
            + '<div class="section-title" style="font-size:1.6rem; margin-top:10px;">Learning by Consensus</div>'
            + "<p>Learning by Consensus is a federated ILP approach in which "
            "multiple clients independently learn symbolic hypotheses from "
            "their local data. Rather than merging the learned rules into a "
            "single global program, the hypotheses are combined at prediction "
            "time through majority voting.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        render_chips(["Popper", "Majority voting", "Ensemble", "Federated Learning", "Symbolic AI"])

    with arch_col:
        st.markdown('<div class="section-title">Architecture</div>', unsafe_allow_html=True)

        with st.container(border=True):
            consensus_figure = ASSETS / "consensus-fig.png"

            if consensus_figure.is_file():
                st.image(
                    str(consensus_figure),
                    caption="Learning by Consensus architecture",
                    use_container_width=True,
                )
            else:
                st.warning(
                    f"Consensus figure not found.\n\nExpected path: `{consensus_figure}`"
                )

    st.divider()

    # ---------------------------------------------------------------
    # How it works
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">How it works</div>', unsafe_allow_html=True)

    st.markdown(
        "Each client $C_i$ learns a local hypothesis $H_i$ using only its "
        "local training partition:"
    )
    st.latex(r"D_i \longrightarrow H_i")

    st.markdown("The learned hypotheses are then collected to form an ensemble:")
    st.latex(r"\mathcal{H} = \{H_1, H_2, \ldots, H_K\}")

    st.markdown(
        "For a new example $e$, every hypothesis independently evaluates "
        "whether the example satisfies the learned target concept:"
    )
    st.latex(r"H_i(e) \in \{\text{POS}, \text{NEG}\}")

    st.markdown(
        "The final prediction is determined using a strict majority vote. "
        "For $K$ hypotheses, the required majority is:"
    )
    st.latex(r"M = \left\lfloor \frac{K}{2} \right\rfloor + 1")

    st.markdown(
        "The consensus predicts **POS** when at least $M$ hypotheses vote "
        "POS; otherwise, it predicts **NEG**."
    )

    st.divider()

    # ---------------------------------------------------------------
    # Visual example
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">A visual example</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.code(
            "Client 1 ──learns──> H1 ──> POS ┐\n"
            "                                 │\n"
            "Client 2 ──learns──> H2 ──> NEG ├──> Majority vote ──> POS\n"
            "                                 │\n"
            "Client 3 ──learns──> H3 ──> POS ┘",
            language=None,
        )
        st.caption("2/3 hypotheses vote POS → Consensus prediction: **POS**")

    st.divider()

    # ---------------------------------------------------------------
    # What is federated?
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">What is federated?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="approach-hero" style="background:#FFFFFF;">'
        "<p>The clients do not jointly construct a single symbolic "
        "hypothesis. Each client performs ILP learning locally on its own "
        "partition and contributes its learned hypothesis to the "
        "consensus mechanism.</p>"
        "<p>The aggregation therefore occurs in the prediction space, "
        "rather than by syntactically merging rules or clauses. The "
        "global behaviour emerges from the agreement and disagreement "
        "between independently learned hypotheses.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    # ---------------------------------------------------------------
    # How an experiment works
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">How an experiment works</div>', unsafe_allow_html=True)

    exp_steps = [
        ("Split train/test", "The original dataset is divided into a global training set and a global test set."),
        ("Partition training data", "Only the training set is partitioned among the K clients."),
        ("Local learning", "Each client independently learns a local hypothesis Hᵢ."),
        ("Collect hypotheses", "The learned hypotheses are collected by the server."),
        ("Evaluate on test set", "Every hypothesis evaluates the same global test examples."),
        ("Majority vote", "Their predictions are aggregated using strict majority voting."),
        ("Compute metrics", "The consensus prediction is compared with the true label to compute Accuracy, Precision, Recall and F1."),
    ]

    row_1 = st.columns(4)
    for col, (idx, (title, body)) in zip(row_1, enumerate(exp_steps[:4], start=1)):
        with col:
            render_step_card(idx, title, body)

    row_2 = st.columns(4)
    for col, (idx, (title, body)) in zip(row_2, enumerate(exp_steps[4:], start=5)):
        with col:
            render_step_card(idx, title, body)

    st.divider()

    # ---------------------------------------------------------------
    # Understanding a consensus decision
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">Understanding a consensus decision</div>', unsafe_allow_html=True)
    st.markdown(
        "Consensus does not hide the individual symbolic decisions behind "
        "the final prediction. For each test example, the platform "
        "reports the vote produced by every learned hypothesis."
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
        "This makes it possible to inspect not only whether the consensus "
        "is correct, but also how much the locally learned hypotheses "
        "agree or disagree on a prediction."
    )

    st.divider()

    # ---------------------------------------------------------------
    # Research paper
    # ---------------------------------------------------------------

    st.markdown('<div class="section-title">📄 Related publication</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            "**Akaichi, Y., Jacquet, J.-M., Linden, I., & Vanhoof, W. (2025).** "
            "[*Federated Inductive Logic Programming for Explainable "
            "Artificial Intelligence.*]"
            "(https://ceur-ws.org/Vol-4059/paper1.pdf) "
            "In Proceedings of the Second Workshop on Explainable "
            "Artificial Intelligence for the Medical Domain (EXPLIMED "
            "2025), CEUR Workshop Proceedings, Vol. 4059, Bologna, Italy."
        )
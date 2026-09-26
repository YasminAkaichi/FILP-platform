from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="Federated Learning | FILP",
    page_icon=":material/hub:",
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
        div[class*="st-key-fl_diagram_img"] [data-testid="stImage"] {{
            display: flex !important;
            justify-content: center !important;
        }}

        .breadcrumb {{
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 4px;
        }}

        .fl-banner {{
            height: 100%;
            display: flex;
            gap: 12px;
            align-items: flex-start;
            padding: 1rem 1.2rem;
            border-radius: 14px;
            background: {PALETTE["primary_soft"]};
            border: 1px solid #D7E0FB;
        }}
        .fl-banner .banner-icon {{ display: flex; align-items: center; flex-shrink: 0; }}
        .fl-banner .banner-body {{ color: {PALETTE["text"]}; font-size: 1.05rem; line-height: 1.55; }}

        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: {PALETTE["text"]};
            margin: 0 0 10px 0;
        }}

        .fl-privacy-note {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: {PALETTE["text_muted"]};
            font-size: 0.88rem;
            margin-top: 14px;
        }}

        .concept-item {{
            display: flex;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 24px;
        }}
        .concept-item .concept-icon {{
            width: 40px;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            padding-top: 2px;
        }}
        .concept-item .concept-icon svg {{
            width: 34px !important;
            height: 34px !important;
        }}
        .concept-item .concept-title {{
            font-weight: 700;
            color: {PALETTE["text"]};
            font-size: 1.35rem;
            margin-bottom: 4px;
        }}
        .concept-item .concept-desc {{
            color: {PALETTE["text_muted"]};
            font-size: 1.15rem;
            line-height: 1.5;
        }}

        .fl-footnote {{
            color: {PALETTE["text_muted"]};
            font-size: 0.82rem;
            font-style: italic;
            line-height: 1.5;
            margin-top: 6px;
        }}

        .coming-soon-card {{
            padding: 2.4rem 2.6rem;
            border-radius: 18px;
            background: {PALETTE["neutral_soft"]};
            border: 1px dashed {PALETTE["border"]};
            text-align: center;
            max-width: 760px;
            margin: 1.5rem auto;
        }}
        .coming-soon-card h3 {{ margin: 0 0 8px 0; color: {PALETTE["text"]}; }}
        .coming-soon-card p {{ color: {PALETTE["text_muted"]}; line-height: 1.6; margin-bottom: 0; }}

        .fl-text-card {{
            padding: 1.6rem 1.8rem;
            border-radius: 16px;
            background: {PALETTE["neutral_soft"]};
            border: 1px solid {PALETTE["border"]};
            max-width: 820px;
        }}
        .fl-text-card p {{
            color: {PALETTE["text_muted"]};
            font-size: 0.95rem;
            line-height: 1.65;
            margin: 0 0 10px 0;
        }}
        .fl-text-card p:last-child {{ margin-bottom: 0; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_style()

st.markdown('<div class="breadcrumb">Home &gt; Federated Learning</div>', unsafe_allow_html=True)

header_left, header_right = st.columns([2.2, 1.3])

with header_left:
    st.title("Federated Learning")
    st.markdown(
        f'<div style="font-size:1.25rem; color:{PALETTE["text_muted"]}; margin-top:-6px;">'
        "Learn across multiple data owners without sharing data.</div>",
        unsafe_allow_html=True,
    )

with header_right:
    banner_icon = (
        '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#0F1B33" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="9" cy="8" r="3"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/>'
        '<path d="M16 4.2c1.5.5 2.5 1.9 2.5 3.5s-1 3-2.5 3.5"/>'
        '<path d="M18.5 14.3c2.2.6 3.5 2.6 3.5 5.7"/></svg>'
    )
    st.markdown(
        '<div class="fl-banner">'
        f'<div class="banner-icon">{banner_icon}</div>'
        '<div class="banner-body">Federated learning enables collaborative model '
        "training while keeping data local, preserving privacy and data "
        "ownership.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

st.write("")

overview_tab, simulation_tab, clients_tab, partitions_tab, communication_tab = st.tabs(
    ["Overview", "Simulation", "Clients", "Data partitions", "Communication"]
)

ICON_COLOR = "#0F1B33"
_ICON_ATTRS = f'viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="{ICON_COLOR}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'

ICON_LOCK = f'<svg {_ICON_ATTRS}><rect x="4.5" y="10.5" width="15" height="9.5" rx="2"/><path d="M7.5 10.5V7a4.5 4.5 0 0 1 9 0v3.5"/></svg>'
ICON_USERS = f'<svg {_ICON_ATTRS}><circle cx="9" cy="8" r="3"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/><path d="M16 4.2c1.5.5 2.5 1.9 2.5 3.5s-1 3-2.5 3.5"/><path d="M18.5 14.3c2.2.6 3.5 2.6 3.5 5.7"/></svg>'
ICON_LINK = f'<svg {_ICON_ATTRS}><path d="M9.5 14.5 14.5 9.5"/><path d="M11 6.5 12.7 4.8a3.5 3.5 0 0 1 5 5L15.9 11.4"/><path d="M13 17.5l-1.7 1.7a3.5 3.5 0 0 1-5-5l1.9-1.9"/></svg>'
ICON_SHIELD = f'<svg {_ICON_ATTRS}><path d="M12 3.5 19 6v5.5c0 4.6-3 7.9-7 9-4-1.1-7-4.4-7-9V6z"/><path d="M9.2 12l1.9 1.9 3.7-3.9"/></svg>'
ICON_EYE = f'<svg {_ICON_ATTRS}><path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="2.6"/></svg>'

CONCEPTS = [
    (ICON_LOCK, "Privacy", "Data remains on local clients."),
    (ICON_USERS, "Collaboration", "Multiple clients contribute to a shared model."),
    (ICON_LINK, "Aggregation", "Model updates or outcomes are combined at the server."),
    (ICON_SHIELD, "Data ownership", "Clients keep control over their data."),
    (ICON_EYE, "Explainability", "Learn logical rules that are interpretable."),
]

with overview_tab:
    diagram_col, concepts_col = st.columns([2.4, 1])

    with diagram_col:
        with st.container(border=True):
            FL_IMAGE_PATH = PROJECT_ROOT / "assets" / "fl.png"
            if FL_IMAGE_PATH.is_file():
                with st.container(key="fl_diagram_img"):
                    st.image(str(FL_IMAGE_PATH), width=748)
            else:
                st.info(
                    "Diagram not found yet.\n\n"
                    f"Drop an image at `assets/fl.png` (expected: `{FL_IMAGE_PATH}`) "
                    "to show the clients-to-server aggregation diagram here."
                )
            st.markdown(
                '<div class="fl-privacy-note">'
                '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#0F1B33" '
                'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
                '<rect x="4.5" y="10.5" width="15" height="9.5" rx="2"/>'
                '<path d="M7.5 10.5V7a4.5 4.5 0 0 1 9 0v3.5"/></svg>'
                " Data stays local. Only model updates or outcomes are shared.</div>",
                unsafe_allow_html=True,
            )

    with concepts_col:
        with st.container(border=True):
            st.markdown('<div class="section-title">Key concepts</div>', unsafe_allow_html=True)
            for icon, title, desc in CONCEPTS:
                st.markdown(
                    '<div class="concept-item">'
                    f'<div class="concept-icon">{icon}</div>'
                    '<div><div class="concept-title">' + title + '</div>'
                    f'<div class="concept-desc">{desc}</div></div>'
                    "</div>",
                    unsafe_allow_html=True,
                )
            st.markdown(
                '<div class="fl-footnote">In FILP, federated learning is combined '
                "with inductive logic programming to obtain interpretable, "
                "privacy-preserving models.</div>",
                unsafe_allow_html=True,
            )

def render_concept_tab(title: str, paragraphs: list[str], link: tuple[str, str] | None = None) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    st.markdown(f'<div class="fl-text-card">{body}</div>', unsafe_allow_html=True)
    if link is not None:
        page, label = link
        st.write("")
        st.page_link(page, label=label)


with simulation_tab:
    render_concept_tab(
        "Why simulate?",
        [
            "FILP runs federated experiments as simulations rather than "
            "on real distributed devices. This makes it possible to test "
            "a protocol without any network infrastructure, while keeping "
            "full control over the number of clients and how the data is "
            "split between them.",
            "It also makes every run exactly reproducible: the same "
            "dataset, partitioning and seed always produce the same "
            "sequence of rounds, which is essential when comparing "
            "Collaboration, Coordination and Consensus on equal footing.",
        ],
        link=("app_pages/04_Simulation.py", "Run a simulation"),
    )

with clients_tab:
    render_concept_tab(
        "What is a client?",
        [
            "A client is a simulated participant that holds one local "
            "partition of a dataset and never shares those raw examples "
            "with anyone else — not with other clients, not with the "
            "server. Keeping data local is the core privacy guarantee of "
            "federated learning.",
            "In FILP specifically, a client does more than compute "
            "gradients: it evaluates or learns symbolic hypotheses "
            "against its own examples and background knowledge, and "
            "returns only a symbolic outcome — never the underlying data.",
        ],
        link=("app_pages/03_FILP_approaches.py", "Compare how each approach uses its clients"),
    )

with partitions_tab:
    render_concept_tab(
        "Why partitioning matters",
        [
            "Splitting a dataset across clients is meant to reflect how "
            "data is realistically distributed in practice — unevenly, "
            "and not necessarily with the same mix of examples on every "
            "client (what's often called a non-IID distribution).",
            "This matters because a federated protocol that performs "
            "well when data is split evenly can behave very differently "
            "when one client holds mostly positive examples and another "
            "mostly negative ones — so testing across partitioning "
            "strategies is part of evaluating an approach honestly.",
        ],
    )

with communication_tab:
    render_concept_tab(
        "What travels between client and server",
        [
            "Classical federated learning exchanges model weights or "
            "gradients between clients and the server. FILP exchanges "
            "something different: symbolic outcomes — a hypothesis' "
            "coverage on a client's data, a score, or a vote — never raw "
            "examples, background knowledge, or numerical parameters.",
            "This is a deliberate choice: because the exchanged "
            "information is symbolic and coarse-grained, it stays close "
            "to human-readable, which is central to FILP's goal of "
            "interpretable, privacy-preserving learning.",
        ],
    )

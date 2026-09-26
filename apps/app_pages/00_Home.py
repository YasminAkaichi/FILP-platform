from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------
# Project setup
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------
# Profile & links — edit the values below, nothing else needs to change
# ---------------------------------------------------------------------

RESEARCHER_NAME = "Yasmine Akaichi"
RESEARCHER_TITLE = (
    "PhD Candidate in Artificial Intelligence | Federated & Interpretable "
    "Machine Learning | Trustworthy AI | Data Engineering & Analytics"
)
RESEARCHER_LOCATION = "Namur, Région wallonne, Belgium"
RESEARCHER_INSTITUTIONS = ["Université de Namur", "Université Clermont Auvergne"]
RESEARCHER_BIO = (
    "AI researcher with a strong interest in building trustworthy, interpretable "
    "and privacy-aware learning systems. My PhD research focuses on Federated "
    "Learning and symbolic AI, at the intersection of machine learning, "
    "explainability, data privacy and responsible AI.\n\n"
    "Alongside research, I enjoy working across the data lifecycle, from data "
    "processing and analysis to engineering pipelines, experimentation and "
    "visualization. My experience combines rigorous research, problem-solving "
    "and scientific communication with hands-on technical skills in Python, "
    "SQL, Docker, cloud and data engineering.\n\n"
    "I am particularly interested in bridging the gap between AI research and "
    "real-world engineering, building systems that are not only effective, but "
    "also understandable, reliable and responsibly designed."
)

LINKEDIN_URL = "https://www.linkedin.com/in/yasmine-akaichi-761975197/"
EMAIL_ADDRESS = "yasmineakaichi02@gmail.com"

# TODO: update once the framework repository is public.
GITHUB_URL = "https://github.com/YasminAkaichi/FILP-platform.git"

# Drop a square photo at this path (e.g. via the assets/ folder). A
# placeholder avatar with your initials is shown until the file exists.
PHOTO_PATH = PROJECT_ROOT / "assets" / "yasmine_akaichi.jpg"

# Vector FILP logo (federated network glyph + wordmark). Swap this file
# for your own artwork later — the page just needs an SVG at this path.
LOGO_PATH = PROJECT_ROOT / "assets" / "filp_logo.svg"


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="FILP Platform — Yasmine Akaichi",
    page_icon=":material/home:",
    layout="wide",
)

if hasattr(st, "logo"):
    try:
        st.logo(str(PROJECT_ROOT / "assets" / "filp_wordmark_white.svg"), size="large")
    except Exception:
        pass




# ---------------------------------------------------------------------
# Visual design system — same accent family as the Experiments and
# Datasets pages, so the whole site reads as one coherent product.
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


def inject_style() -> None:
    # Every HTML snippet below is written as a single line with no
    # leading indentation — Streamlit's markdown renderer treats a
    # blank line followed by 4+ spaces of indentation as a code block,
    # which silently breaks custom HTML cards otherwise.
    st.markdown(
        f"""
        <style>
        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            padding-left: 2.2rem;
            padding-right: 2.2rem;
            max-width: 100% !important;
        }}

        button[data-testid="stBaseButton-primary"],
        button[data-testid="stBaseButton-primary"] * {{
            color: #FFFFFF !important;
        }}
        button[data-testid^="stBaseButton"] {{
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        button[data-testid^="stBaseButton"] div {{
            display: flex !important;
            align-items: center !important;
        }}
        button[data-testid^="stBaseButton"] p {{
            margin: 0 !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            line-height: 1 !important;
        }}

        div[class*="st-key-hero_card"] {{
            padding: 2.6rem 3rem;
            border-radius: 22px;
            background: linear-gradient(135deg, #F3F8FE 0%, #EAF2FC 100%);
            border: 1px solid #DCE9FA;
            margin-top: 0.8rem;
            margin-bottom: 1.6rem;
        }}
        div[class*="st-key-hero_card"] .eyebrow {{
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.78rem;
            color: {PALETTE["text_muted"]};
            font-weight: 700;
            margin-bottom: 0.7rem;
        }}
        div[class*="st-key-hero_card"] h1 {{
            font-size: 2.7rem;
            font-weight: 800;
            margin: 0 0 0.5rem 0;
            color: {PALETTE["text"]};
        }}
        div[class*="st-key-hero_card"] .subtitle {{
            font-size: 1.15rem;
            font-weight: 600;
            color: {PALETTE["text"]};
            margin-bottom: 0.7rem;
        }}
        div[class*="st-key-hero_card"] p {{
            font-size: 0.98rem;
            color: {PALETTE["text_muted"]};
            max-width: 620px;
            line-height: 1.65;
            margin-bottom: 1.2rem;
        }}

        .venn-wrap {{
            position: relative;
            height: 230px;
        }}
        .venn-circle {{
            position: absolute;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            font-size: 0.78rem;
            font-weight: 700;
            color: {PALETTE["text"]};
        }}
        .venn-quote {{
            font-style: italic;
            color: {PALETTE["text_muted"]};
            font-size: 0.92rem;
            text-align: center;
            margin-top: 10px;
        }}

        .feature-chip {{
            display: inline-block;
            padding: 0.4rem 0.85rem;
            margin: 0.2rem 0.35rem 0.2rem 0;
            border-radius: 999px;
            background: {PALETTE["primary_soft"]};
            color: {PALETTE["primary"]};
            font-size: 0.85rem;
            font-weight: 600;
        }}

        .section-title {{
            font-size: 1.35rem;
            font-weight: 700;
            color: {PALETTE["text"]};
            margin: 0 0 4px 0;
        }}
        .section-caption {{
            font-size: 0.92rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 14px;
        }}

        .concept-card {{
            min-height: 210px;
            padding: 1.5rem;
            border: 1px solid {PALETTE["border"]};
            border-radius: 16px;
            background: {PALETTE["bg_card"]};
        }}
        .concept-card h3 {{
            margin-top: 0;
            color: {PALETTE["text"]};
        }}
        .concept-card p {{
            color: {PALETTE["text_muted"]};
            line-height: 1.55;
        }}

        .filp-flow {{
            display: flex;
            align-items: stretch;
            justify-content: space-between;
            gap: 1rem;
            margin: 0.6rem 0 1.8rem 0;
        }}
        .flow-box {{
            flex: 1;
            padding: 1.3rem;
            border-radius: 16px;
            text-align: center;
            border: 1px solid {PALETTE["border"]};
            background: {PALETTE["primary_soft"]};
        }}
        .flow-box h4 {{ margin: 0 0 6px 0; color: {PALETTE["text"]}; }}
        .flow-box p {{ margin: 0; color: {PALETTE["text_muted"]}; font-size: 0.88rem; line-height: 1.5; }}
        .flow-arrow {{
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            color: {PALETTE["primary"]};
        }}

        .avatar-placeholder {{
            width: 100%;
            aspect-ratio: 1 / 1;
            border-radius: 20px;
            background: linear-gradient(135deg, {PALETTE["primary"]}, #8fa8ea);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.6rem;
            font-weight: 700;
            letter-spacing: 0.05em;
        }}

        .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 12px 0; }}
        .chip {{ border-radius: 999px; padding: 4px 12px; font-size: 0.8rem; font-weight: 500; }}
        .chip-neutral {{ background: {PALETTE["neutral_soft"]}; color: {PALETTE["text"]}; }}
        .chip-primary {{ background: {PALETTE["primary_soft"]}; color: {PALETTE["primary"]}; }}

        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
        }}

        .contact-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 10px;
            color: white !important;
            font-size: 0.88rem;
            font-weight: 600;
            text-decoration: none !important;
            margin: 0 8px 8px 0;
        }}
        .contact-pill:hover {{ opacity: 0.9; }}

        @media (max-width: 900px) {{
            .filp-flow {{ flex-direction: column; }}
            .flow-arrow {{ transform: rotate(90deg); }}
            div[class*="st-key-hero_card"] h1 {{ font-size: 2.1rem; }}
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


def render_chips(labels: list[str], variant: str = "neutral") -> None:
    chips = "".join(f'<span class="chip chip-{variant}">{label}</span>' for label in labels)
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)


def render_badge(text: str, kind: str = "success") -> str:
    color, bg = (
        (PALETTE["success"], PALETTE["success_soft"])
        if kind == "success"
        else (PALETTE["neutral"], PALETTE["neutral_soft"])
    )
    return f'<span class="badge" style="color:{color};background:{bg};">{text}</span>'


# Small brand-accurate icons (inline SVG, no external file needed) used
# by the contact pills below.
ICON_LINKEDIN = (
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">'
    '<path d="M20.45 20.45h-3.55v-5.57c0-1.33-.02-3.04-1.85-3.04-1.86 0-2.15 1.45-2.15 2.94v5.67H9.35V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.59 0 4.25 2.37 4.25 5.45v6.29zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.56V9h3.56v11.45z"/>'
    "</svg>"
)
ICON_EMAIL = (
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">'
    '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>'
    "</svg>"
)
ICON_GITHUB = (
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">'
    '<path d="M12 2C6.48 2 2 6.58 2 12.19c0 4.49 2.87 8.3 6.84 9.65.5.1.68-.22.68-.49v-1.9c-2.78.62-3.37-1.19-3.37-1.19-.46-1.2-1.11-1.51-1.11-1.51-.91-.64.07-.63.07-.63 1 .07 1.53 1.05 1.53 1.05.9 1.57 2.34 1.12 2.91.86.09-.66.35-1.12.64-1.38-2.22-.26-4.56-1.14-4.56-5.06 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.31.1-2.73 0 0 .84-.28 2.75 1.05a9.3 9.3 0 0 1 5 0c1.91-1.33 2.75-1.05 2.75-1.05.55 1.42.2 2.47.1 2.73.64.72 1.03 1.63 1.03 2.75 0 3.93-2.34 4.79-4.57 5.05.36.32.68.94.68 1.9v2.82c0 .27.18.6.69.49A10.02 10.02 0 0 0 22 12.19C22 6.58 17.52 2 12 2z"/>'
    "</svg>"
)


def render_contact_pill(icon_svg: str, label: str, href: str, bg: str) -> str:
    return (
        f'<a href="{href}" target="_blank" rel="noopener" class="contact-pill" '
        f'style="background:{bg};">{icon_svg}<span>{label}</span></a>'
    )


# ---------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------

inject_style()

with st.container(key="hero_card"):
    hero_text_col, hero_illustration_col = st.columns([1.4, 1.6])

    with hero_text_col:
        st.markdown(
            '<div class="eyebrow">Symbolic AI · Privacy · Explainability</div>'
            "<h1>Welcome to FILP</h1>"
            '<div class="subtitle">A platform for Federated Inductive Logic Programming</div>'
            "<p>Design, run and analyse experiments that combine inductive "
            "logic programming and federated learning, with a focus on "
            "interpretability, privacy and real-world applications.</p>",
            unsafe_allow_html=True,
        )

        cta_left, cta_right, _ = st.columns([1.3, 1.3, 2])
        with cta_left:
            if st.button(
                "Simulation",
                type="primary",
                icon=":material/play_arrow:",
                use_container_width=True,
            ):
                st.switch_page("app_pages/04_Simulation.py")
        with cta_right:
            if st.button(
                "View experiments",
                icon=":material/arrow_forward:",
                use_container_width=True,
            ):
                st.switch_page("app_pages/05_Experiments.py")

    with hero_illustration_col:
        HERO_FIGURE_PATH = PROJECT_ROOT / "assets" / "flxILP.png"
        if HERO_FIGURE_PATH.is_file():
            hero_img_left, hero_img_center, hero_img_right = st.columns([1, 4, 1])
            with hero_img_center:
                st.image(str(HERO_FIGURE_PATH), width=380)
                st.markdown(
                    '<div class="venn-quote" style="width:380px;">'
                    '"Simple rules for complex worlds."</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.warning(f"Hero figure not found.\n\nExpected path: `{HERO_FIGURE_PATH}`")

st.write("")


# ---------------------------------------------------------------------
# Platform capabilities (matches the mockup's four cards) — flat,
# single-colour line icons instead of emoji, to match the app's theme.
# ---------------------------------------------------------------------

CAPABILITY_ICON_COLOR = "#0F1B33"

ICON_FLASK = (
    f'<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="{CAPABILITY_ICON_COLOR}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M9 3h6M10 3v6.5L4.8 18a1.5 1.5 0 0 0 1.3 2.2h11.8a1.5 1.5 0 0 0 1.3-2.2L14 9.5V3"/>'
    '<path d="M7.5 15h9"/>'
    "</svg>"
)
ICON_DATABASE = (
    f'<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="{CAPABILITY_ICON_COLOR}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<ellipse cx="12" cy="5.5" rx="7" ry="2.5"/>'
    '<path d="M5 5.5v13c0 1.38 3.13 2.5 7 2.5s7-1.12 7-2.5v-13"/>'
    '<path d="M5 12c0 1.38 3.13 2.5 7 2.5s7-1.12 7-2.5"/>'
    "</svg>"
)
ICON_DOCUMENT = (
    f'<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="{CAPABILITY_ICON_COLOR}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M7 3h7l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/>'
    '<path d="M14 3v4h4"/>'
    '<path d="M9 12.5h6M9 16h6"/>'
    "</svg>"
)
ICON_NETWORK = (
    f'<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="{CAPABILITY_ICON_COLOR}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="5" r="2.2"/><circle cx="5" cy="18" r="2.2"/><circle cx="19" cy="18" r="2.2"/>'
    '<path d="M12 7.2 6.3 16M12 7.2 17.7 16M7.2 18h9.6"/>'
    "</svg>"
)
ICON_CHART = (
    f'<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="{CAPABILITY_ICON_COLOR}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'
    "</svg>"
)
ICON_REPEAT = (
    f'<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="{CAPABILITY_ICON_COLOR}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M4 12a8 8 0 0 1 13.66-5.66L20 8"/><path d="M20 4v4h-4"/>'
    '<path d="M20 12a8 8 0 0 1-13.66 5.66L4 16"/><path d="M4 20v-4h4"/>'
    "</svg>"
)


def render_capability_header(icon_svg: str, title: str) -> None:
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;">'
        f'{icon_svg}<span style="font-weight:700; color:{PALETTE["text"]};">{title}</span></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Concepts
# ---------------------------------------------------------------------

st.markdown('<div class="section-title">The two ideas behind FILP</div>', unsafe_allow_html=True)
st.write("")

symbolic_column, federated_column = st.columns(2)

with symbolic_column:
    st.markdown(
        '<div class="concept-card">'
        "<h3>Symbolic Artificial Intelligence</h3>"
        "<p>Symbolic AI represents knowledge explicitly through logical "
        "facts, rules and relations. Unlike purely numerical models, "
        "symbolic systems produce human-readable hypotheses expressed "
        "as logic programs.</p>"
        "<p>In this platform, Popper learns compact Prolog programs from "
        "positive examples, negative examples, background knowledge and "
        "a declarative bias.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

with federated_column:
    st.markdown(
        '<div class="concept-card">'
        "<h3>Federated Learning</h3>"
        "<p>Federated Learning enables several clients to collaborate "
        "without centralising their raw datasets. Each client keeps its "
        "examples locally and communicates only the information required "
        "by the learning protocol.</p>"
        "<p>FILP extends this principle to symbolic learning, where "
        "clients evaluate logic programs and return symbolic feedback to "
        "a coordinating server.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

st.write("")

st.markdown(
    '<div class="section-title">From local logical data to a federated hypothesis</div>',
    unsafe_allow_html=True,
)
st.write("")

st.markdown(
    '<div class="filp-flow">'
    '<div class="flow-box"><h4>Local clients</h4>'
    "<p>Positive and negative examples<br>Local background knowledge<br>Private dataset partitions</p></div>"
    '<div class="flow-arrow">→</div>'
    '<div class="flow-box"><h4>Federated protocol</h4>'
    "<p>Hypothesis distribution<br>Local symbolic evaluation<br>Aggregated feedback</p></div>"
    '<div class="flow-arrow">→</div>'
    '<div class="flow-box"><h4>Logic program</h4>'
    "<p>Human-readable rules<br>Global solution<br>Explainable hypothesis</p></div>"
    "</div>",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Research roadmap
# ---------------------------------------------------------------------

st.markdown('<div class="section-title">Research roadmap</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-caption">FILP is designed as a family of collaboration engines</div>',
    unsafe_allow_html=True,
)

roadmap_items = [
    ("Learning by Collaboration", "Implemented and available in this platform.", "success"),
    ("Learning by Coordination", "Implemented and available in this platform.", "success"),
    ("Learning by Consensus", "Implemented and available in this platform.", "success"),
]

roadmap_columns = st.columns(3)

for column, (title, description, kind) in zip(roadmap_columns, roadmap_items):
    with column:
        with st.container(border=True):
            badge_label = "Available" if kind == "success" else "Planned"
            st.markdown(render_badge(badge_label, kind), unsafe_allow_html=True)
            st.markdown(f"**{title}**")
            st.caption(description)

st.write("")
st.divider()


# ---------------------------------------------------------------------
# Pipeline overview
# ---------------------------------------------------------------------

st.markdown('<div class="section-title">How FILP works</div>', unsafe_allow_html=True)

PIPELINE_IMAGE_PATH = PROJECT_ROOT / "assets" / "FILP-Pipeline.png"

if PIPELINE_IMAGE_PATH.is_file():
    st.image(str(PIPELINE_IMAGE_PATH), use_container_width=True)
else:
    st.warning(f"Pipeline figure not found.\n\nExpected path: `{PIPELINE_IMAGE_PATH}`")

st.write("")
st.divider()


# ---------------------------------------------------------------------
# Platform Capabilities
# ---------------------------------------------------------------------

st.markdown('<div class="section-title">Platform Capabilities</div>', unsafe_allow_html=True)
st.write("")

mockup_columns = st.columns(4)

with mockup_columns[0]:
    with st.container(border=True):
        render_capability_header(ICON_FLASK, "Experiments")
        st.caption("Launch and compare approaches.")
        st.page_link("app_pages/05_Experiments.py", label="Open")

with mockup_columns[1]:
    with st.container(border=True):
        render_capability_header(ICON_DATABASE, "Datasets")
        st.caption("Inspect examples and background knowledge.")
        st.page_link("app_pages/02_Inductive_logic_programming.py", label="Open")

with mockup_columns[2]:
    with st.container(border=True):
        render_capability_header(ICON_CHART, "Monitoring")
        st.caption("Inspect hypotheses and execution times.")
        st.page_link("app_pages/05_Experiments.py", label="Open")

with mockup_columns[3]:
    with st.container(border=True):
        render_capability_header(ICON_REPEAT, "Reproducibility")
        st.caption("Simulate federated scenarios, clients and benchmarks.")
        st.page_link("app_pages/05_Experiments.py", label="Open")

st.write("")
st.divider()


# The "About the researcher" bio now lives on its own page (pages/08_About.py),
# reachable from the sidebar — see that file for its content.

st.write("")
st.caption(f"© {RESEARCHER_NAME} · FILP Platform")
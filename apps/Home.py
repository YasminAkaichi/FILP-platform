from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------
# Project setup
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

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
    page_icon="",
    layout="wide",
)

# st.logo() renders in a fixed slot above the page navigation menu in
# the sidebar (Home / Experiments / Datasets), on every page. This is
# the app-wide branding spot — call it identically on each page.
if hasattr(st, "logo"):
    try:
        st.logo(str(LOGO_PATH), size="large")
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
            padding-top: 2rem;
            padding-bottom: 3rem;
        }}

        .filp-hero {{
            padding: 3rem 3.2rem;
            border-radius: 22px;
            background:
                radial-gradient(circle at top left, rgba(91, 127, 222, 0.28), transparent 40%),
                radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.20), transparent 40%),
                linear-gradient(135deg, #111827 0%, #1f2937 50%, #0f172a 100%);
            color: white;
            margin-bottom: 1.6rem;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
        }}
        .filp-hero .eyebrow {{
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.78rem;
            color: #93c5fd;
            font-weight: 600;
            margin-bottom: 0.6rem;
        }}
        .filp-hero h1 {{
            font-size: 2.9rem;
            margin: 0 0 0.6rem 0;
            color: white;
        }}
        .filp-hero p {{
            font-size: 1.1rem;
            color: #dbeafe;
            max-width: 820px;
            line-height: 1.7;
            margin-bottom: 1.2rem;
        }}

        .feature-chip {{
            display: inline-block;
            padding: 0.4rem 0.85rem;
            margin: 0.2rem 0.35rem 0.2rem 0;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.12);
            color: #e0e7ff;
            font-size: 0.85rem;
            font-weight: 600;
            border: 1px solid rgba(255, 255, 255, 0.18);
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
            .filp-hero h1 {{ font-size: 2.1rem; }}
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

st.markdown(
    '<div class="filp-hero">'
    '<div class="eyebrow">PhD Thesis · Federated &amp; Symbolic AI</div>'
    "<h1>FILP Platform</h1>"
    "<p>An experimentation platform for Federated Inductive Logic "
    "Programming (FILP), combining symbolic reasoning, distributed "
    "learning, reproducible experiment management and detailed "
    "scientific analysis. Built as part of my PhD research.</p>"
    '<div>'
    '<span class="feature-chip">Symbolic AI</span>'
    '<span class="feature-chip">Federated Learning</span>'
    '<span class="feature-chip">Inductive Logic Programming</span>'
    '<span class="feature-chip">Reproducible Experiments</span>'
    '<span class="feature-chip">Explainable AI</span>'
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

cta_left, cta_mid, cta_right = st.columns(3)

with cta_left:
    st.page_link("pages/3_Experiments.py", label="Run an experiment", use_container_width=True)
with cta_mid:
    st.page_link("pages/2_Datasets.py", label="Explore the datasets", icon="📚", use_container_width=True)


st.write("")
st.divider()


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
# Platform capabilities
# ---------------------------------------------------------------------

st.markdown('<div class="section-title">Platform capabilities</div>', unsafe_allow_html=True)
st.write("")

capability_columns = st.columns(4)

with capability_columns[0]:
    with st.container(border=True):
        st.markdown("**🧪 Experiments**")
        st.caption("Launch and reproduce FILP benchmarks with configurable parameters.")
        st.page_link("pages/3_Experiments.py", label="Open")

with capability_columns[1]:
    with st.container(border=True):
        st.markdown("**📚 Datasets**")
        st.caption("Inspect examples, background knowledge and language bias for every dataset.")
        st.page_link("pages/2_Datasets.py", label="Open")

with capability_columns[2]:
    with st.container(border=True):
        st.markdown("**📈 Monitoring**")
        st.caption("Track hypotheses, rounds, client evaluations and execution times.")

with capability_columns[3]:
    with st.container(border=True):
        st.markdown("**🔁 Reproducibility**")
        st.caption("Fixed seeds, versioned configurations and full run history for every experiment.")

st.write("")
st.divider()


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
    ("Learning by Coordination", "Planned as an additional FILP engine.", "neutral"),
    ("Learning by Consensus", "Planned as an additional FILP engine.", "neutral"),
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
# About the researcher — deliberately placed near the bottom: visitors
# land on the platform itself first, and reach the "who built this"
# section only once they've seen what it does.
# ---------------------------------------------------------------------

st.markdown('<div class="section-title">About the researcher</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-caption">The person behind this framework</div>',
    unsafe_allow_html=True,
)

photo_column, bio_column = st.columns([1, 3])

with photo_column:
    if PHOTO_PATH.is_file():
        st.image(str(PHOTO_PATH), use_container_width=True)
    else:
        initials = "".join(part[0] for part in RESEARCHER_NAME.split()[:2]).upper()
        st.markdown(f'<div class="avatar-placeholder">{initials}</div>', unsafe_allow_html=True)
        try:
            relative_hint = PHOTO_PATH.relative_to(PROJECT_ROOT)
        except ValueError:
            relative_hint = PHOTO_PATH
        st.caption(f"Add a photo at `{relative_hint}`")

with bio_column:
    st.markdown(f'<div class="section-title">{RESEARCHER_NAME}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-caption" style="margin-bottom:6px;">{RESEARCHER_TITLE}</div>',
        unsafe_allow_html=True,
    )
    render_chips([RESEARCHER_LOCATION, *RESEARCHER_INSTITUTIONS], variant="neutral")
    st.write(RESEARCHER_BIO)

    st.markdown(
        render_contact_pill(ICON_LINKEDIN, "LinkedIn", LINKEDIN_URL, "#0A66C2")
        + render_contact_pill(ICON_EMAIL, "Email", f"mailto:{EMAIL_ADDRESS}", PALETTE["primary"])
        + render_contact_pill(ICON_GITHUB, "GitHub", GITHUB_URL, "#1F2430"),
        unsafe_allow_html=True,
    )

st.write("")
st.caption(f"© {RESEARCHER_NAME} · FILP Platform")
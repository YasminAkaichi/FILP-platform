from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------
# Profile & links
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
EMAIL_ADDRESS = "ya.akaichi@gmail.com"
GITHUB_URL = "https://github.com/YasminAkaichi/FILP-platform.git"

PHOTO_PATH = PROJECT_ROOT / "assets" / "yasmine_akaichi.jpg"


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="About | FILP",
    page_icon="",
    layout="wide",
)

if hasattr(st, "logo"):
    try:
        st.logo(str(PROJECT_ROOT / "assets" / "filp_wordmark_white.svg"), size="large")
    except Exception:
        pass

with st.sidebar:
    st.markdown(
        '<div style="margin-top:24px; padding:10px 10px; display:flex; align-items:center; '
        'gap:10px; border-top:1px solid #22314F;">'
        '<div style="width:32px; height:32px; border-radius:50%; background:#3E63DE; color:#fff; '
        'display:flex; align-items:center; justify-content:center; font-weight:700; flex-shrink:0;">Y</div>'
        '<div style="line-height:1.3;">'
        '<div style="font-weight:700; color:#FFFFFF; font-size:0.88rem;">Yasmine</div>'
        '<div style="font-size:0.75rem; color:#AEB9D4;">PhD Candidate</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


PALETTE = {
    "bg_card": "#F6F8FC",
    "border": "#E2E8F5",
    "text_muted": "#5B6472",
    "text": "#1F2430",
    "primary": "#5B7FDE",
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
    section[data-testid="stSidebar"] * {{
        color: #AEB9D4 !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{
        border-radius: 10px;
        margin: 2px 10px;
        padding: 6px 10px !important;
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
    section[data-testid="stSidebar"] > div:first-child {{
        display: flex;
        flex-direction: column;
        height: 100vh;
    }}
    section[data-testid="stSidebarNav"] {{
        flex: 1 1 auto;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
    }}
    section[data-testid="stSidebarNav"] ul,
    section[data-testid="stSidebarNavItems"] {{
        display: flex;
        flex-direction: column;
        height: 100%;
        flex: 1 1 auto;
    }}
    section[data-testid="stSidebarNav"] ul li:nth-last-child(2),
    section[data-testid="stSidebarNavItems"] > li:nth-last-child(2) {{
        margin-top: auto !important;
        padding-top: 10px;
        border-top: 1px solid #22314F;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: #22314F !important;
    }}

    .section-title {{
        font-size: 1.35rem;
        font-weight: 700;
        line-height: 1.4;
        color: {PALETTE["text"]};
        margin: 0 0 4px 0;
        padding-top: 2px;
    }}
    .section-caption {{
        font-size: 0.92rem;
        color: {PALETTE["text_muted"]};
        margin-bottom: 14px;
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
    </style>
    """,
    unsafe_allow_html=True,
)


def render_chips(labels: list[str], variant: str = "neutral") -> None:
    chips = "".join(f'<span class="chip chip-{variant}">{label}</span>' for label in labels)
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)


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
# Page body
# ---------------------------------------------------------------------

st.markdown('<div class="section-title">About</div>', unsafe_allow_html=True)
st.caption("Who built FILP, and how to reach me.")

photo_column, bio_column = st.columns([1, 3])

with photo_column:
    if PHOTO_PATH.is_file():
        st.image(str(PHOTO_PATH), width=150)
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

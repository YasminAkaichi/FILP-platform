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
    "bg_page": "#F5F6F9",
    "bg_card": "#F6F8FC",
    "border": "#E2E8F5",
    "text_muted": "#5B6472",
    "text": "#1F2430",
    "primary": "#3E63DE",
    "primary_soft": "#EAF0FE",
    "neutral_soft": "#EEF1F6",
    "success": "#2F9E63",
    "success_soft": "#E3F5EC",
    "error": "#D64545",
    "error_soft": "#FBEAEA",
    "warning": "#C98A1F",
    "warning_soft": "#FCF1DE",
    "violet": "#7C5CFC",
    "violet_soft": "#F1ECFE",
}

NAVY = "#0F1B33"

ICONS = {
    "lock": '<rect x="4.5" y="10.5" width="15" height="9.5" rx="2"/><path d="M7.5 10.5V7a4.5 4.5 0 0 1 9 0v3.5"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/><path d="M16 4.2c1.5.5 2.5 1.9 2.5 3.5s-1 3-2.5 3.5"/><path d="M18.5 14.3c2.2.6 3.5 2.6 3.5 5.7"/>',
    "shield": '<path d="M12 3.5 19 6v5.5c0 4.6-3 7.9-7 9-4-1.1-7-4.4-7-9V6z"/><path d="M9.2 12l1.9 1.9 3.7-3.9"/>',
    "database": '<ellipse cx="12" cy="6" rx="7.5" ry="3"/><path d="M4.5 6v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V6"/><path d="M4.5 12v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-6"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.3l2.6 2.6L16.2 9"/>',
    "x": '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
    "warning": '<path d="M12 3.5 21 19.5H3z"/><path d="M12 9.5v4.3"/><path d="M12 16.7h.01"/>',
    "zap": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "star": '<path d="M12 3.5l2.6 5.6 6.1.6-4.6 4.1 1.3 6-5.4-3.2-5.4 3.2 1.3-6-4.6-4.1 6.1-.6z"/>',
    "wifi": '<path d="M2.5 8.5a15 15 0 0 1 19 0"/><path d="M5.8 12.2a10 10 0 0 1 12.4 0"/><path d="M9.2 15.8a5 5 0 0 1 5.6 0"/><circle cx="12" cy="19.2" r="1" fill="currentColor" stroke="none"/>',
    "settings": '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v3M12 18.5v3M4.6 4.6l2.1 2.1M17.3 17.3l2.1 2.1M2.5 12h3M18.5 12h3M4.6 19.4l2.1-2.1M17.3 6.7l2.1-2.1"/>',
    "layers": '<path d="M12 3 2.5 8l9.5 5 9.5-5z"/><path d="M2.5 13l9.5 5 9.5-5"/><path d="M2.5 18l9.5 5 9.5-5"/>',
    "link": '<path d="M9.5 14.5 14.5 9.5"/><path d="M11 6.5 12.7 4.8a3.5 3.5 0 0 1 5 5L15.9 11.4"/><path d="M13 17.5l-1.7 1.7a3.5 3.5 0 0 1-5-5l1.9-1.9"/>',
    "target": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/>',
    "heart": '<path d="M12 20.3S3.2 14.7 3.2 8.9c0-3 2.4-5.4 5.3-5.4 1.8 0 3.4.9 4.2 2.4.8-1.5 2.4-2.4 4.2-2.4 2.9 0 5.3 2.4 5.3 5.4 0 5.8-9 11.4-9 11.4z"/>',
    "building": '<rect x="5" y="3" width="14" height="18" rx="1"/><path d="M9 7.5h2M13 7.5h2M9 11.5h2M13 11.5h2M9 15.5h2M13 15.5h2"/>',
    "smartphone": '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
    "factory": '<path d="M3.5 21V10l5.5 3.8V10l5.5 3.8V7l5.5 3.8V21z"/><path d="M3.5 21h16.5"/>',
    "eye": '<path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="2.6"/>',
}


def icon(name: str, color: str = NAVY, size: int = 20, stroke: float = 1.6) -> str:
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" '
        f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'
    )


def inject_style() -> None:
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"], [data-testid="stMain"], .stApp {{
            background: {PALETTE["bg_page"]};
        }}
        .block-container {{
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            padding-top: 3rem;
            padding-bottom: 3rem;
            padding-left: 2.2rem;
            padding-right: 2.2rem;
            max-width: 100% !important;
            background: {PALETTE["bg_page"]};
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

        div[data-testid="stHorizontalBlock"] {{ align-items: stretch !important; }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{ display: flex !important; }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div {{ width: 100%; height: 100%; }}

        div[class*="st-key-fl_card_glance"] {{
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        div[class*="st-key-fl_card_glance"] img {{
            max-height: 320px !important;
            width: auto !important;
            object-fit: contain;
            display: block;
            margin: 0 auto;
        }}

        div[class*="st-key-fl_card_"] {{
            background: #FFFFFF;
            border: 1.5px solid {PALETTE["border"]};
            border-radius: 16px;
            padding: 1.3rem 1.5rem;
            height: 100%;
            box-sizing: border-box;
        }}

        .breadcrumb {{
            font-size: 0.85rem;
            color: {PALETTE["text_muted"]};
            margin-bottom: 4px;
        }}

        .fl-card-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: {PALETTE["text"]};
            margin-bottom: 8px;
        }}
        .fl-card-text {{
            color: {PALETTE["text"]};
            font-size: 0.95rem;
            line-height: 1.6;
            margin-bottom: 14px;
        }}

        .fl-mini-box {{
            border-radius: 12px;
            padding: 14px 16px;
            height: 100%;
            box-sizing: border-box;
        }}
        .fl-mini-box .mini-icon {{
            width: 32px; height: 32px; border-radius: 8px; background: #FFFFFF;
            display: flex; align-items: center; justify-content: center; margin-bottom: 10px;
        }}
        .fl-mini-box .mini-title {{ font-weight: 700; font-size: 0.92rem; color: {PALETTE["text"]}; margin-bottom: 4px; }}
        .fl-mini-box .mini-desc {{ font-size: 0.82rem; color: {PALETTE["text_muted"]}; line-height: 1.45; }}

        .fl-feature-row {{ display: flex; gap: 12px; align-items: flex-start; margin-bottom: 16px; }}
        .fl-feature-row:last-child {{ margin-bottom: 0; }}
        .fl-feature-row .feature-icon {{
            width: 32px; height: 32px; border-radius: 8px; flex-shrink: 0;
            display: flex; align-items: center; justify-content: center;
        }}
        .fl-feature-row .feature-title {{ font-weight: 700; font-size: 0.92rem; color: {PALETTE["text"]}; margin-bottom: 2px; }}
        .fl-feature-row .feature-desc {{ font-size: 0.83rem; color: {PALETTE["text_muted"]}; line-height: 1.42; }}

        .fl-compare-header {{
            font-weight: 700; font-size: 0.92rem; padding: 8px 12px; border-radius: 8px;
            margin-bottom: 12px; text-align: center;
        }}
        .fl-compare-row {{ display: flex; gap: 8px; align-items: flex-start; margin-bottom: 10px; font-size: 0.82rem; color: {PALETTE["text_muted"]}; line-height: 1.4; }}
        .fl-compare-row:last-child {{ margin-bottom: 0; }}
        .fl-compare-row .compare-icon {{ flex-shrink: 0; margin-top: 1px; }}

        .fl-step {{ display: flex; gap: 14px; position: relative; padding-bottom: 18px; }}
        .fl-step:last-child {{ padding-bottom: 0; }}
        .fl-step .step-line {{
            position: absolute; left: 15px; top: 32px; bottom: -18px; width: 2px; background: {PALETTE["border"]};
        }}
        .fl-step:last-child .step-line {{ display: none; }}
        .fl-step .step-num {{
            width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
            color: #FFFFFF; font-weight: 700; font-size: 0.85rem; flex-shrink: 0; position: relative; z-index: 1;
        }}
        .fl-step .step-title {{ font-weight: 700; font-size: 0.92rem; color: {PALETTE["text"]}; margin-bottom: 2px; }}
        .fl-step .step-desc {{ font-size: 0.83rem; color: {PALETTE["text_muted"]}; line-height: 1.45; }}

        .fl-privacy-note {{
            display: flex; align-items: center; gap: 8px; color: {PALETTE["text_muted"]};
            font-size: 0.83rem; margin-top: 14px;
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

st.title("Federated Learning")
st.markdown(
    f'<div style="font-size:1.2rem; color:{PALETTE["text_muted"]}; margin-top:-6px;">'
    "Learn from distributed data without sharing it.</div>",
    unsafe_allow_html=True,
)

st.write("")

overview_tab, workflow_tab, privacy_tab, types_tab, applications_tab = st.tabs(
    ["Overview", "Workflow", "Privacy & Security", "Types of FL", "Applications"]
)


def mini_box(icon_name: str, color: str, bg: str, title: str, desc: str) -> str:
    return (
        f'<div class="fl-mini-box" style="background:{bg};">'
        f'<div class="mini-icon">{icon(icon_name, color, 18)}</div>'
        f'<div class="mini-title">{title}</div>'
        f'<div class="mini-desc">{desc}</div>'
        "</div>"
    )


def feature_row(icon_name: str, color: str, bg: str, title: str, desc: str) -> str:
    return (
        '<div class="fl-feature-row">'
        f'<div class="feature-icon" style="background:{bg};">{icon(icon_name, color, 16)}</div>'
        f'<div><div class="feature-title">{title}</div><div class="feature-desc">{desc}</div></div>'
        "</div>"
    )


def compare_row(icon_name: str, color: str, text: str) -> str:
    return (
        '<div class="fl-compare-row">'
        f'<span class="compare-icon">{icon(icon_name, color, 15)}</span><span>{text}</span>'
        "</div>"
    )


def step_row(number: int, color: str, title: str, desc: str, last: bool = False) -> str:
    line = "" if last else '<div class="step-line"></div>'
    return (
        f'<div class="fl-step">{line}'
        f'<div class="step-num" style="background:{color};">{number}</div>'
        f'<div><div class="step-title">{title}</div><div class="step-desc">{desc}</div></div>'
        "</div>"
    )


with overview_tab:
    what_col, glance_col = st.columns([1.3, 1])

    with what_col:
        with st.container(key="fl_card_what"):
            st.markdown('<div class="fl-card-title">What is Federated Learning (FL)?</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="fl-card-text">Federated Learning (FL) is a distributed machine learning '
                "paradigm that allows multiple participants (clients) to collaboratively train a model "
                "without sharing their local data. Each client keeps its data locally and only shares "
                "model updates or aggregated information with a central server.</div>",
                unsafe_allow_html=True,
            )
            mb_1, mb_2 = st.columns(2)
            with mb_1:
                st.markdown(
                    mini_box("lock", PALETTE["violet"], PALETTE["violet_soft"], "Data stays local", "Raw data never leaves the client."),
                    unsafe_allow_html=True,
                )
                st.write("")
                st.markdown(
                    mini_box("shield", PALETTE["success"], PALETTE["success_soft"], "Privacy-preserving", "Reduces the risk of exposing sensitive data."),
                    unsafe_allow_html=True,
                )
            with mb_2:
                st.markdown(
                    mini_box("users", PALETTE["primary"], PALETTE["primary_soft"], "Collaborative learning", "Multiple clients contribute to a shared model."),
                    unsafe_allow_html=True,
                )
                st.write("")
                st.markdown(
                    mini_box("database", PALETTE["violet"], PALETTE["violet_soft"], "Global model", "The server aggregates client contributions to improve the model."),
                    unsafe_allow_html=True,
                )

    with glance_col:
        with st.container(key="fl_card_glance"):
            FL_IMAGE_PATH = PROJECT_ROOT / "assets" / "fl.png"
            if FL_IMAGE_PATH.is_file():
                st.image(str(FL_IMAGE_PATH), width="stretch")
            else:
                st.info(f"Diagram not found at `{FL_IMAGE_PATH}`.")

    st.write("")

    key_col, compare_col, workflow_col = st.columns(3)

    with key_col:
        with st.container(key="fl_card_keychar"):
            st.markdown('<div class="fl-card-title" style="font-size:1.05rem;">Key characteristics</div>', unsafe_allow_html=True)
            st.markdown(
                feature_row("layers", PALETTE["violet"], PALETTE["violet_soft"], "Distributed data", "Data is partitioned and owned by multiple participants."),
                unsafe_allow_html=True,
            )
            st.markdown(
                feature_row("lock", PALETTE["primary"], PALETTE["primary_soft"], "Data privacy", "Clients keep their data locally (e.g., for legal, regulatory or organizational reasons)."),
                unsafe_allow_html=True,
            )
            st.markdown(
                feature_row("settings", PALETTE["success"], PALETTE["success_soft"], "Central aggregation", "The server aggregates model updates to obtain a global model."),
                unsafe_allow_html=True,
            )
            st.markdown(
                feature_row("users", PALETTE["primary"], PALETTE["primary_soft"], "Collaborative learning", "Multiple clients contribute to a common learning objective."),
                unsafe_allow_html=True,
            )
            st.markdown(
                feature_row("shield", PALETTE["violet"], PALETTE["violet_soft"], "Applicable to real-world settings", "Especially useful when data is sensitive, large-scale or spread across organizations."),
                unsafe_allow_html=True,
            )

    with compare_col:
        with st.container(key="fl_card_compare"):
            st.markdown('<div class="fl-card-title" style="font-size:1.05rem;">Comparison with centralized learning</div>', unsafe_allow_html=True)
            cmp_a, cmp_b = st.columns(2)
            with cmp_a:
                st.markdown(
                    f'<div class="fl-compare-header" style="background:{PALETTE["neutral_soft"]}; color:{PALETTE["text"]};">Centralized Learning</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(compare_row("x", PALETTE["error"], "All data collected in one place"), unsafe_allow_html=True)
                st.markdown(compare_row("warning", PALETTE["warning"], "Higher privacy and legal risks"), unsafe_allow_html=True)
                st.markdown(compare_row("database", PALETTE["primary"], "Trains a single model"), unsafe_allow_html=True)
                st.markdown(compare_row("zap", PALETTE["success"], "Simple infrastructure"), unsafe_allow_html=True)
                st.markdown(compare_row("x", PALETTE["error"], "May not be possible due to data ownership (e.g., GDPR)"), unsafe_allow_html=True)
            with cmp_b:
                st.markdown(
                    f'<div class="fl-compare-header" style="background:{PALETTE["primary_soft"]}; color:{PALETTE["primary"]};">Federated Learning</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(compare_row("check", PALETTE["success"], "Data stays on each client"), unsafe_allow_html=True)
                st.markdown(compare_row("check", PALETTE["success"], "Better privacy and regulatory compliance"), unsafe_allow_html=True)
                st.markdown(compare_row("users", PALETTE["primary"], "Collaborative model training"), unsafe_allow_html=True)
                st.markdown(compare_row("link", PALETTE["warning"], "Requires coordination and aggregation"), unsafe_allow_html=True)
                st.markdown(compare_row("star", PALETTE["violet"], "Enables learning from distributed, sensitive data"), unsafe_allow_html=True)

    with workflow_col:
        with st.container(key="fl_card_workflow_mini"):
            st.markdown('<div class="fl-card-title" style="font-size:1.05rem;">Typical federated learning workflow</div>', unsafe_allow_html=True)
            st.markdown(step_row(1, PALETTE["violet"], "Initialization", "The server initializes a global model and sends it to clients."), unsafe_allow_html=True)
            st.markdown(step_row(2, PALETTE["primary"], "Local training", "Each client trains the model on its local data."), unsafe_allow_html=True)
            st.markdown(step_row(3, PALETTE["success"], "Model updates", "Clients send model updates (e.g., gradients or parameters) to the server (not raw data)."), unsafe_allow_html=True)
            st.markdown(step_row(4, PALETTE["violet"], "Aggregation", "The server aggregates the updates to obtain a new global model (e.g., using FedAvg)."), unsafe_allow_html=True)
            st.markdown(step_row(5, PALETTE["primary"], "Repeat", "The process is repeated for several communication rounds until convergence.", last=True), unsafe_allow_html=True)

    st.write("")

    why_col, challenges_col = st.columns(2)

    with why_col:
        with st.container(key="fl_card_why"):
            st.markdown('<div class="fl-card-title" style="font-size:1.05rem;">Why use federated learning?</div>', unsafe_allow_html=True)
            why_a, why_b, why_c, why_d = st.columns(4)
            with why_a:
                st.markdown(
                    mini_box("lock", PALETTE["violet"], PALETTE["violet_soft"], "Privacy & data control", "Keep sensitive data local (e.g., personal, medical, financial)."),
                    unsafe_allow_html=True,
                )
            with why_b:
                st.markdown(
                    mini_box("shield", PALETTE["primary"], PALETTE["primary_soft"], "Regulatory compliance", "Helps meet regulations such as GDPR."),
                    unsafe_allow_html=True,
                )
            with why_c:
                st.markdown(
                    mini_box("link", PALETTE["success"], PALETTE["success_soft"], "Access to more data", "Learn from distributed data that cannot be centralized."),
                    unsafe_allow_html=True,
                )
            with why_d:
                st.markdown(
                    mini_box("users", PALETTE["primary"], PALETTE["primary_soft"], "Real-world applicability", "Suitable for organizations, hospitals, companies, and mobile devices."),
                    unsafe_allow_html=True,
                )

    with challenges_col:
        with st.container(key="fl_card_challenges"):
            st.markdown('<div class="fl-card-title" style="font-size:1.05rem;">Challenges</div>', unsafe_allow_html=True)
            ch_a, ch_b, ch_c, ch_d = st.columns(4)
            with ch_a:
                st.markdown(
                    mini_box("database", PALETTE["error"], PALETTE["error_soft"], "Data heterogeneity", "Clients may have non-IID data distributions."),
                    unsafe_allow_html=True,
                )
            with ch_b:
                st.markdown(
                    mini_box("wifi", PALETTE["warning"], PALETTE["warning_soft"], "Communication cost", "Repeated model updates can be expensive."),
                    unsafe_allow_html=True,
                )
            with ch_c:
                st.markdown(
                    mini_box("warning", PALETTE["warning"], PALETTE["warning_soft"], "Security risks", "Model updates can still leak information and are vulnerable to attacks."),
                    unsafe_allow_html=True,
                )
            with ch_d:
                st.markdown(
                    mini_box("settings", PALETTE["primary"], PALETTE["primary_soft"], "Algorithm design", "Need robust aggregation and methods that handle distributed and heterogeneous data."),
                    unsafe_allow_html=True,
                )


def render_text_card(title: str, paragraphs: list[str], link: tuple[str, str] | None = None) -> None:
    st.markdown(f'<div class="fl-card-title">{title}</div>', unsafe_allow_html=True)
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    st.markdown(f'<div class="fl-text-card">{body}</div>', unsafe_allow_html=True)
    if link is not None:
        page, label = link
        st.write("")
        st.page_link(page, label=label)


with workflow_tab:
    wf_left, wf_right = st.columns([1.4, 1])
    with wf_left:
        with st.container(key="fl_card_workflow_detail"):
            st.markdown('<div class="fl-card-title">How a federated learning round works</div>', unsafe_allow_html=True)
            st.markdown(step_row(1, PALETTE["violet"], "Initialization", "The server defines a model architecture (or, in FILP, a hypothesis language and bias) and sends the starting point to every participating client."), unsafe_allow_html=True)
            st.markdown(step_row(2, PALETTE["primary"], "Local training", "Each client trains — or, in FILP, searches for or evaluates a hypothesis — using only its own local examples and background knowledge."), unsafe_allow_html=True)
            st.markdown(step_row(3, PALETTE["success"], "Model updates", "Clients send back updates to the server: gradients and parameters in classical FL, or symbolic outcomes (coverage, scores, votes) in FILP — never the raw data itself."), unsafe_allow_html=True)
            st.markdown(step_row(4, PALETTE["violet"], "Aggregation", "The server combines every client's contribution into a new global model or consensus hypothesis, using a rule such as FedAvg (weighted averaging) or, in FILP, a voting or coverage-based aggregation."), unsafe_allow_html=True)
            st.markdown(step_row(5, PALETTE["primary"], "Repeat", "Steps 1-4 repeat for several communication rounds. FILP runs this as a reproducible simulation, so the same dataset, partitioning and seed always produce the same sequence of rounds.", last=True), unsafe_allow_html=True)

    with wf_right:
        with st.container(key="fl_card_workflow_note"):
            render_text_card(
                "Why simulate?",
                [
                    "FILP runs federated experiments as simulations rather than on real distributed "
                    "devices. This makes it possible to test a protocol without any network "
                    "infrastructure, while keeping full control over the number of clients and how "
                    "the data is split between them.",
                    "It also makes every run exactly reproducible, which is essential when comparing "
                    "Collaboration, Coordination and Consensus on equal footing.",
                ],
                link=("app_pages/04_Simulation.py", "Run a simulation"),
            )


with privacy_tab:
    priv_left, priv_right = st.columns([1.3, 1])
    with priv_left:
        with st.container(key="fl_card_privacy_main"):
            st.markdown('<div class="fl-card-title">What leaves the client</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="fl-card-text">In federated learning, raw examples, patient records or private '
                "documents never leave the device or organization that owns them. Only a compact summary "
                "of what was learned — a gradient, a set of parameters, or in FILP's case a symbolic outcome "
                "such as a hypothesis' coverage, a score or a vote — is sent to the server.</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                feature_row("lock", PALETTE["violet"], PALETTE["violet_soft"], "Data never centralized", "Each client's dataset stays on its own machine for the entire experiment."),
                unsafe_allow_html=True,
            )
            st.markdown(
                feature_row("eye", PALETTE["primary"], PALETTE["primary_soft"], "Coarse-grained exchange", "FILP exchanges symbolic outcomes rather than numerical gradients, which stay closer to human-readable and expose less about individual records."),
                unsafe_allow_html=True,
            )
            st.markdown(
                feature_row("warning", PALETTE["warning"], PALETTE["warning_soft"], "Not a full guarantee", "Even without sharing raw data, model updates can still leak information (e.g., via model inversion or membership inference attacks) — FL reduces exposure, it does not eliminate every risk."),
                unsafe_allow_html=True,
            )

    with priv_right:
        with st.container(key="fl_card_privacy_side"):
            render_text_card(
                "Strengthening privacy further",
                [
                    "Production federated learning deployments often add extra protections on top of "
                    "the base protocol: secure aggregation (so the server only ever sees an aggregate, "
                    "never an individual client's update) and differential privacy (adding calibrated "
                    "noise so no single record can be reconstructed from the output).",
                    "This platform focuses on the algorithmic mechanics of privacy-preserving, "
                    "interpretable federated learning — data never leaving the client, and only "
                    "symbolic outcomes being exchanged. Teams deploying this in production should "
                    "layer in additional protections such as those above depending on their threat model.",
                ],
            )


with types_tab:
    types_top_left, types_top_right = st.columns(2)
    with types_top_left:
        with st.container(key="fl_card_types_topology"):
            st.markdown('<div class="fl-card-title" style="font-size:1.1rem;">By data topology</div>', unsafe_allow_html=True)
            st.markdown(
                feature_row("layers", PALETTE["primary"], PALETTE["primary_soft"], "Horizontal FL", "Clients share the same feature space but hold different examples — e.g., several hospitals each with their own patients but the same type of records."),
                unsafe_allow_html=True,
            )
            st.markdown(
                feature_row("link", PALETTE["violet"], PALETTE["violet_soft"], "Vertical FL", "Clients hold different features for overlapping entities — e.g., a bank and a retailer holding different data about the same customers."),
                unsafe_allow_html=True,
            )

    with types_top_right:
        with st.container(key="fl_card_types_scale"):
            st.markdown('<div class="fl-card-title" style="font-size:1.1rem;">By deployment scale</div>', unsafe_allow_html=True)
            st.markdown(
                feature_row("building", PALETTE["success"], PALETTE["success_soft"], "Cross-silo", "A small number of reliable, always-available participants — typically organizations such as hospitals, banks or companies."),
                unsafe_allow_html=True,
            )
            st.markdown(
                feature_row("smartphone", PALETTE["primary"], PALETTE["primary_soft"], "Cross-device", "Many, often unreliable participants — typically phones or edge devices that connect intermittently."),
                unsafe_allow_html=True,
            )

    st.write("")

    with st.container(key="fl_card_types_partition"):
        st.markdown('<div class="fl-card-title" style="font-size:1.1rem;">By data distribution</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="fl-card-text">How a dataset is split across clients matters as much as the '
            "protocol itself. An IID (independent and identically distributed) split spreads examples "
            "evenly, while a non-IID split reflects how data is realistically distributed in practice — "
            "unevenly, with one client possibly holding mostly positive examples and another mostly "
            "negative ones. A federated protocol that performs well under IID data can behave very "
            "differently under non-IID data, so testing across both is part of evaluating an approach "
            "honestly.</div>",
            unsafe_allow_html=True,
        )

    st.write("")

    with st.container(key="fl_card_types_approaches"):
        render_text_card(
            "The four approaches on this platform",
            [
                "FILP implements and compares four ways of turning inductive logic programming into a "
                "federated protocol: a Centralized baseline (all data in one place, for reference), "
                "Collaboration, Coordination and Consensus — each distributing the ILP search across "
                "clients differently.",
            ],
            link=("app_pages/03_FILP_approaches.py", "Compare the four approaches"),
        )


with applications_tab:
    app_a, app_b, app_c, app_d = st.columns(4)
    with app_a:
        with st.container(key="fl_card_app_health"):
            st.markdown(
                mini_box("heart", PALETTE["violet"], PALETTE["violet_soft"], "Healthcare", "Hospitals collaboratively learn diagnostic models — e.g., predicting malignancy from mammography findings — without pooling patient records."),
                unsafe_allow_html=True,
            )
    with app_b:
        with st.container(key="fl_card_app_finance"):
            st.markdown(
                mini_box("building", PALETTE["primary"], PALETTE["primary_soft"], "Finance", "Banks jointly train fraud-detection models across institutions without sharing individual transaction data."),
                unsafe_allow_html=True,
            )
    with app_c:
        with st.container(key="fl_card_app_mobile"):
            st.markdown(
                mini_box("smartphone", PALETTE["success"], PALETTE["success_soft"], "Mobile devices", "Keyboards and voice assistants improve predictive text and speech models from on-device usage, without uploading what users type or say."),
                unsafe_allow_html=True,
            )
    with app_d:
        with st.container(key="fl_card_app_iot"):
            st.markdown(
                mini_box("factory", PALETTE["violet"], PALETTE["violet_soft"], "Industry & IoT", "Factories and sensor networks learn shared predictive-maintenance models across sites without exposing proprietary operational data."),
                unsafe_allow_html=True,
            )

    st.write("")

    with st.container(key="fl_card_app_filp"):
        render_text_card(
            "Where FILP fits in",
            [
                "This platform targets the healthcare-style scenario above: several institutions, each "
                "holding sensitive, relational data (patients, mammography findings, biopsy results), "
                "that want to learn a single, interpretable model together without ever centralizing "
                "raw records. Because ILP produces first-order logic rules rather than opaque weights, "
                "the resulting model stays readable by the domain experts who have to trust it — see the "
                "breast-cancer example on the Inductive Logic Programming page for a concrete "
                "illustration of the kind of rule this platform is built to learn.",
            ],
            link=("app_pages/02_Inductive_logic_programming.py", "See the ILP breast-cancer example"),
        )


st.markdown(
    '<div style="margin-top:auto; padding-top:1.2rem; border-top:1px solid #E2E8F5; color:#5B6472; font-size:0.85rem;">© Yasmine Akaichi · FILP Platform</div>',
    unsafe_allow_html=True,
)

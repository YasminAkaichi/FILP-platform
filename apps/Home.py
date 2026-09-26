from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------
# Central navigation — page order, titles and (white, Material) icons
# all live here. Individual page files still set their own page_title
# / favicon via st.set_page_config, but the sidebar label and icon
# shown to the user are controlled by this list.
# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
# Global sidebar styling — injected once, here, before any individual
# page runs. Every page file also injects this same block for when it
# is opened directly, but having it here too means the dark sidebar is
# already in place the instant the app shell loads, instead of
# flashing the default light sidebar for a moment on every navigation.
# ---------------------------------------------------------------------

st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        background: #0F1B33 !important;
        border-right: 1px solid #22314F;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
        height: auto !important;
        min-height: 0 !important;
        margin-bottom: 4px !important;
        padding-top: 6px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] img,
    section[data-testid="stSidebar"] [data-testid="stLogo"] {
        height: 76px !important;
        max-height: none !important;
        width: auto !important;
        max-width: 100% !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        min-height: 100vh !important;
        display: flex !important;
        flex-direction: column !important;
    }
    [data-testid="stSidebarNav"] {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 auto !important;
        min-height: 0 !important;
    }
    [data-testid="stSidebarNavItems"] {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 auto !important;
    }
    [data-testid="stSidebarNavItems"] li:nth-last-of-type(2) {
        margin-top: auto !important;
        padding-top: 303px;
        border-top: 1px solid #22314F;
    }
    section[data-testid="stSidebar"] * {
        color: #C7D2EC !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
        border-radius: 10px;
        margin: 2px 8px 2px 0 !important;
        padding: 8px 8px 8px 4px !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a > span:first-child {
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        flex-shrink: 0 !important;
        width: auto !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a [data-testid="stIconMaterial"] {
        width: 27px !important;
        height: 27px !important;
        min-width: 27px !important;
        font-size: 27px !important;
        margin: 0 !important;
        padding: 0 !important;
        color: #E4EAFB !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a > span:last-child {
        font-size: 18px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] [data-testid="stIconMaterial"] {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
        background: #1B2A4C !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: #1B2A4C !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] * {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #22314F !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

pages = [
    st.Page("app_pages/00_Home.py", title="Home", icon=":material/home:", default=True),
    st.Page("app_pages/01_Federated_Learning.py", title="Federated Learning", icon=":material/hub:"),
    st.Page("app_pages/02_Inductive_logic_programming.py", title="ILP", icon=":material/psychology:"),
    st.Page("app_pages/03_FILP_approaches.py", title="FILP approaches", icon=":material/compare_arrows:"),
    st.Page("app_pages/04_Simulation.py", title="Simulation", icon=":material/play_circle:"),
    st.Page("app_pages/05_Experiments.py", title="Experiments", icon=":material/science:"),
    st.Page("app_pages/06_Analytics.py", title="Analytics", icon=":material/monitoring:"),
    st.Page("app_pages/07_Documentation.py", title="Documentation", icon=":material/menu_book:"),
    st.Page("app_pages/08_About.py", title="About", icon=":material/info:"),
]

pg = st.navigation(pages, position="sidebar")
pg.run()

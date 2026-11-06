"""Shared responsive layer for every FILP page.

It is injected once, from the app entry point (apps/Home.py), so it applies
to all pages. It only *adapts* sizes to the screen (13"/14" MacBook, external
monitors, very large displays); it does not change colors, content or logic.

Rules are written with `!important` and slightly higher specificity than the
per-page styles, so they win without editing those pages.
"""

from __future__ import annotations

import streamlit as st

RESPONSIVE_CSS = """
<style>
/* ------------------------------------------------------------------ */
/* Fluid type: ~16px on a 13"/14" laptop, up to 18px on large screens  */
/* ------------------------------------------------------------------ */
html {
    font-size: clamp(14px, 0.3vw + 12.2px, 18px) !important;
}

/* ------------------------------------------------------------------ */
/* Main content: fluid side padding, centered and capped on huge screens */
/* ------------------------------------------------------------------ */
div.block-container {
    padding-left: clamp(1rem, 2.2vw, 3.2rem) !important;
    padding-right: clamp(1rem, 2.2vw, 3.2rem) !important;
    padding-top: clamp(2rem, 4vh, 3rem) !important;
    padding-bottom: clamp(2rem, 4vh, 3rem) !important;
    max-width: min(100%, 1800px) !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* ------------------------------------------------------------------ */
/* Sidebar: the gap above "Documentation / About" was a fixed 303px,   */
/* which overflowed on short laptop screens. It now scales with the    */
/* window height (same 303px on tall screens).                         */
/* ------------------------------------------------------------------ */
[data-testid="stSidebarNavItems"] li:nth-last-of-type(2) {
    padding-top: clamp(0px, 30vh, 303px) !important;
}

/* ------------------------------------------------------------------ */
/* Sidebar logo: the FILP flower with its name needs more than 64px     */
/* ------------------------------------------------------------------ */
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] img,
section[data-testid="stSidebar"] [data-testid="stLogo"] {
    height: 96px !important;
    width: auto !important;
    max-width: 100% !important;
}

/* ------------------------------------------------------------------ */
/* Components that should never overflow their box                      */
/* ------------------------------------------------------------------ */
.badge {
    white-space: nowrap;
}
.metric-card .metric-value,
.kv-value {
    overflow-wrap: anywhere;
}
.kv-row {
    gap: 12px;
}
div[data-testid="stCode"] pre,
div[data-testid="stMarkdownContainer"] pre {
    overflow-x: auto;
}
div[data-testid="stDataFrame"],
div[data-testid="stTable"] {
    max-width: 100%;
}
[data-testid="stImage"] img {
    max-width: 100%;
    height: auto;
}

/* ------------------------------------------------------------------ */
/* Smaller windows (13" MacBook with a narrow window, split screen)     */
/* ------------------------------------------------------------------ */
@media (max-width: 1100px) {
    div.block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .metric-card {
        padding: 10px 12px;
    }
    .metric-card .metric-value {
        font-size: 1.15rem;
    }
}

/* ------------------------------------------------------------------ */
/* Very large screens: slightly roomier cards                           */
/* ------------------------------------------------------------------ */
@media (min-width: 2000px) {
    .metric-card {
        padding: 16px 18px;
    }
}
</style>
"""


def inject_responsive_css() -> None:
    """Inject the shared responsive stylesheet (call once per run)."""
    st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)

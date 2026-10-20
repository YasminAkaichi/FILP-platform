"""
Streamlit widget that follows a BackgroundRun and offers the "Stop" button.

Usage (in a page):

    bg = st.session_state.get("my_run")
    if bg is not None and not bg.done:
        render_run_monitor(bg, key="my_run", title="Running Popper…")
        st.stop()          # nothing else to draw while it runs
    if bg is not None and bg.done:
        ...read bg.result / bg.error / bg.stopped_without_result...
        st.session_state.pop("my_run")

The monitor refreshes itself every 1.5 s (st.fragment) and triggers a full
rerun of the page as soon as the run is over, so the page can show the
result.
"""

from __future__ import annotations

import streamlit as st

from core.background_run import BackgroundRun


def _format_elapsed(seconds: float) -> str:
    seconds = int(seconds)
    minutes, secs = divmod(seconds, 60)
    return f"{minutes}:{secs:02d}"


def render_run_monitor(
    bg: BackgroundRun,
    key: str,
    title: str = "Running…",
    details: str | None = None,
) -> None:
    @st.fragment(run_every=1.5)
    def _monitor() -> None:
        if bg.done:
            st.rerun()  # full rerun: the page picks up the result
            return

        with st.container(border=True):
            st.markdown(f"**{title}**")
            if details:
                st.caption(details)

            if bg.stop_requested:
                st.info(
                    "Stopping — waiting for the best result found so far "
                    f"(elapsed {_format_elapsed(bg.elapsed)})…"
                )
            else:
                st.caption(f"Elapsed: {_format_elapsed(bg.elapsed)}")
                st.button(
                    "⏹ Stop and keep the best result so far",
                    key=f"{key}_stop",
                    on_click=bg.stop,
                    help=(
                        "Ends the search now and saves the best hypothesis "
                        "found up to this point. Andante and Learning by "
                        "Consensus cannot return a partial result: stopping "
                        "them discards the run."
                    ),
                )

    _monitor()

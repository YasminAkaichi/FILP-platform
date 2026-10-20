"""
Graceful "Stop" for the centralized Popper runners (popper-core and Popper-v3).

Both engines implement their timeout with signal.alarm(): a SIGALRM handler
raises an exception inside the search, which is caught and makes
learn_solution() return the best program found so far. Pressing "Stop" in
the UI should give exactly that result immediately instead of waiting for
the timeout.

The UI writes <output-dir>/STOP (core/run_control.py). A small watcher
thread in the runner notices the file and triggers the engine's own SIGALRM
handler — but only while the search is running and only once, so that the
handler can never fire while the runner is loading data or writing its
result file (where the exception would not be caught).

Nothing in the vendored Popper code is modified.
"""

from __future__ import annotations

import os
import signal
import threading
import time
from contextlib import contextmanager

_state = {"active": False, "fired": False}


def _on_stop_signal(signum, frame):
    handler = signal.getsignal(signal.SIGALRM)
    if _state["active"] and not _state["fired"] and callable(handler):
        _state["fired"] = True
        handler(signal.SIGALRM, frame)  # the engine's timeout handler


def install_stop_watcher(output_dir) -> None:
    """Start watching <output_dir>/STOP. No-op where SIGUSR1 does not exist
    (Windows): there, the launcher's grace-period kill is the fallback."""
    if not hasattr(signal, "SIGUSR1"):
        return
    signal.signal(signal.SIGUSR1, _on_stop_signal)
    stop_file = os.path.join(str(output_dir), "STOP")

    def watch() -> None:
        while not _state["fired"]:
            if os.path.exists(stop_file) and _state["active"]:
                # Re-sent every half second until the engine's handler has
                # been installed and has fired (it is installed a moment
                # after the search starts).
                os.kill(os.getpid(), signal.SIGUSR1)
            time.sleep(0.5)

    threading.Thread(target=watch, daemon=True, name="StopWatcher").start()


@contextmanager
def search_running():
    """Wrap the call to learn_solution(): the stop signal is only honoured
    inside this block."""
    _state["active"] = True
    try:
        yield
    finally:
        _state["active"] = False

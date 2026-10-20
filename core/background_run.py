"""
Run an experiment in a background thread, so the UI stays responsive and can
offer a "Stop" button.

Streamlit executes a page script top to bottom; if the script blocks on
`launcher.run(...)`, no button can act until it returns. Here the run lives
in its own thread, and the page only polls `done` (see apps/run_monitor.py).
The thread never touches Streamlit.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable

from core.run_control import RunControl, RunStopped


class BackgroundRun:
    def __init__(self, target: Callable[[RunControl], Any]) -> None:
        """target receives the RunControl and returns the run's result
        (e.g. a benchmark id or an experiment id)."""
        self.control = RunControl()
        self.result: Any = None
        self.error: BaseException | None = None
        self.stopped_without_result = False
        self.started_at = time.time()
        self.finished_at: float | None = None
        self._target = target
        self._thread = threading.Thread(
            target=self._main,
            daemon=True,
            name="BackgroundRun",
        )
        self._thread.start()

    def _main(self) -> None:
        try:
            self.result = self._target(self.control)
        except RunStopped:
            self.stopped_without_result = True
        except BaseException as error:  # noqa: BLE001 — surfaced to the UI
            self.error = error
        finally:
            self.finished_at = time.time()

    @property
    def done(self) -> bool:
        return self.finished_at is not None

    @property
    def elapsed(self) -> float:
        return (self.finished_at or time.time()) - self.started_at

    @property
    def stop_requested(self) -> bool:
        return self.control.stop_requested

    def stop(self) -> None:
        self.control.request_stop()

"""
Cooperative "Stop" for a running experiment.

How it works
------------
The UI runs an experiment in a background thread and keeps a `RunControl`
for it. `RunControl.request_stop()` does two things:

  1. it sets a flag the launcher polls while it waits for the engines;
  2. it writes an empty file called STOP into the experiment's artifacts
     directory.

Every search engine watches for that file in the very place where it
already checks its timeout, and reacts exactly as if the timeout had
expired: it stops searching, keeps the BEST hypothesis found so far, writes
its result file and exits normally. The launcher then reads that result
like any other run. So "Stop" means "give me what you have now", not
"throw everything away".

Engines that cannot return a partial result (Andante, which has no
timeout of its own, and the Consensus learners) do not react to the file;
after a grace period the launcher terminates their processes and the
experiment is saved with status STOPPED.

The file name is the contract between this module and the engines; the
engines test it inline (os.path.exists) so they need no import from here.
"""

from __future__ import annotations

import threading
from pathlib import Path

STOP_FILENAME = "STOP"


class RunControl:
    def __init__(self) -> None:
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._directories: list[Path] = []
        # Same list object the launcher fills with its subprocesses (see
        # ExperimentLauncher.run's process_tracker); lets a last-resort
        # hard stop terminate them.
        self.process_tracker: dict = {}

    @property
    def stop_requested(self) -> bool:
        return self._event.is_set()

    def register_directory(self, directory: Path) -> None:
        """Called by the launcher as soon as an experiment directory
        exists. If Stop was already requested, the STOP file is written
        immediately so the engine sees it from its first check."""
        directory = Path(directory)
        with self._lock:
            self._directories.append(directory)
            already = self._event.is_set()
        if already:
            self._write_stop_file(directory)

    def request_stop(self) -> None:
        with self._lock:
            self._event.set()
            directories = list(self._directories)
        for directory in directories:
            self._write_stop_file(directory)

    @staticmethod
    def _write_stop_file(directory: Path) -> None:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            (directory / STOP_FILENAME).write_text("stop\n", encoding="utf-8")
        except OSError:
            pass  # the grace-period kill in the launcher is the fallback


class RunStopped(Exception):
    """Raised inside the launcher when a run was stopped by the user and
    has no result to save."""

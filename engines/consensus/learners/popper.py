"""Popper-v4 adapter for the Consensus engine.

Training and prediction are executed in isolated subprocesses so that
each client has an independent SWI-Prolog state.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

from pathlib import Path
from typing import Any


class PopperConsensusLearner:

    def __init__(
        self,
        dataset_path: str | Path,
        timeout: int = 600,
        debug: bool = False,
        show_stats: bool = False,
    ) -> None:

        self.dataset_path = Path(dataset_path).resolve()
        self.timeout = timeout
        self.debug = debug
        self.show_stats = show_stats

        self._validate_dataset()


    def _validate_dataset(self) -> None:

        if not self.dataset_path.is_dir():
            raise FileNotFoundError(
                f"Dataset directory not found: "
                f"{self.dataset_path}"
            )

        required_files = (
            "bias.pl",
            "bk.pl",
            "exs.pl",
        )

        missing = [
            filename
            for filename in required_files
            if not (
                self.dataset_path / filename
            ).is_file()
        ]

        if missing:
            raise FileNotFoundError(
                f"Invalid Popper dataset "
                f"{self.dataset_path}. "
                f"Missing: {', '.join(missing)}"
            )


    def learn(
        self,
    ) -> tuple[list[str], Any, Any]:

        env = os.environ.copy()

        project_root = Path(__file__).resolve().parents[3]
        popper_v4_path = project_root / "symbolic" / "popper-v4"

        existing_pythonpath = env.get("PYTHONPATH", "")

        python_paths = [
            str(popper_v4_path),
            str(project_root),
        ]

        if existing_pythonpath:
            python_paths.append(existing_pythonpath)

        env["PYTHONPATH"] = os.pathsep.join(
            python_paths
        )

        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "engines.consensus.learners.popper_trainer",
                "--dataset",
                str(self.dataset_path),
                "--timeout",
                str(self.timeout),
            ],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )

        # Popper logs may be written to stderr.
        if process.stderr:
            print(
                process.stderr,
                file=sys.stderr,
                end="",
            )

        result = json.loads(
            process.stdout.strip()
        )

        hypothesis = result.get(
            "hypothesis",
            [],
        )

        score = result.get(
            "score",
        )

        # Stats are not serialized yet.
        stats = None

        return hypothesis, score, stats


    def predict(
        self,
        hypothesis: list[str],
        test_dataset: str | Path,
    ) -> dict[str, bool]:

        test_dataset = Path(
            test_dataset
        ).resolve()

        if not test_dataset.is_dir():
            raise FileNotFoundError(
                f"Test dataset not found: "
                f"{test_dataset}"
            )

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            encoding="utf-8",
            delete=False,
        ) as file:

            json.dump(
                hypothesis,
                file,
                ensure_ascii=False,
            )

            hypothesis_file = file.name

        try:

            env = os.environ.copy()

            process = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "engines.consensus.learners.popper_predictor",
                    "--test-dataset",
                    str(test_dataset),
                    "--hypothesis-file",
                    hypothesis_file,
                ],
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )

            if process.stderr:
                print(
                    process.stderr,
                    file=sys.stderr,
                    end="",
                )

            predictions = json.loads(
                process.stdout.strip()
            )

            return {
                example_id: bool(prediction)
                for example_id, prediction
                in predictions.items()
            }

        finally:

            Path(
                hypothesis_file
            ).unlink(
                missing_ok=True
            )
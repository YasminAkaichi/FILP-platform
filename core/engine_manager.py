from pathlib import Path

import yaml


class EngineManager:
    def __init__(self, config_path: str = "config/paths.yaml") -> None:
        self.config_path = Path(config_path)
        self.engines = self._load_engines()

    def _load_engines(self) -> dict[str, Path]:
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )

        with self.config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        if not config or "engines" not in config:
            raise ValueError("The configuration must contain an 'engines' section.")

        return {
            name: Path(path).expanduser()
            for name, path in config["engines"].items()
        }

    def get_engine_path(self, engine_name: str) -> Path:
        if engine_name not in self.engines:
            available = ", ".join(self.engines.keys())
            raise ValueError(
                f"Unknown engine '{engine_name}'. Available engines: {available}"
            )

        engine_path = self.engines[engine_name]

        if not engine_path.exists():
            raise FileNotFoundError(
                f"Engine directory not found: {engine_path}"
            )

        return engine_path
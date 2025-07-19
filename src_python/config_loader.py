from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import yaml

@dataclass
class RunConfig:
    """Lightweight container for parameters that drive a ChaseHound run.

    The structure is intentionally unopinionated for now – any key/value pairs
    present in the YAML file are exposed through the *params* attribute so that
    future logic can decide how to interpret them.  You can extend this class
    later with explicit, typed fields once the configuration surface stabilises.
    """

    params: Dict[str, Any]

    @classmethod
    def from_yaml(cls, path: str | Path) -> "RunConfig":
        """Load a YAML configuration file located at *path* and return an
        instance of *RunConfig*.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file '{path}' not found")

        with path.open("r", encoding="utf-8") as fp:
            data = yaml.safe_load(fp) or {}

        if not isinstance(data, dict):
            raise ValueError("Top-level YAML content must be a mapping/dictionary.")

        return cls(params=data)

    def get(self, key: str, default: Any | None = None) -> Any | None:
        """Convenience helper mimicking *dict.get* semantics."""
        return self.params.get(key, default)

    def __getitem__(self, item: str) -> Any:
        return self.params[item]

    def __contains__(self, item: str) -> bool:
        return item in self.params 
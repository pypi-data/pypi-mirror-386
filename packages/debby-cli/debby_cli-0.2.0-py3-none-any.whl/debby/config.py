from pathlib import Path
from types import ModuleType
from typing import Any
import tomlkit


class CheckConfig:
    def __init__(self, check_module: ModuleType, **custom_params: dict[str, Any]):
        self.enabled = custom_params.pop(
            "enabled", getattr(check_module, "enabled", True)
        )
        self.skip = custom_params.pop("skip", getattr(check_module, "skip", list()))
        self.skip_tags = custom_params.pop("skip_tags", list())
        self.skip_paths = custom_params.pop("skip_paths", list())
        self.custom_params = custom_params

    def param(self, name: str):
        return self.custom_params.get(name, None)


class Config:

    def __init__(self, **extras: dict[str, Any]):
        self._extras = extras

    def get_check_config(
        self, check_name: str, check_module: ModuleType
    ) -> CheckConfig:
        custom_params = self._extras.get(check_name, dict())
        return CheckConfig(check_module, **custom_params)

    @classmethod
    def from_path(cls, path: Path):
        raw = path.read_text()
        parsed = tomlkit.parse(raw)
        return cls(**parsed)

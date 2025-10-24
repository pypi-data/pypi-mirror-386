import os
from typing import Iterable, Any
from types import ModuleType
from pathlib import Path
from importlib import import_module
from debby import checks
from debby.core import Check
from debby.config import Config


class Collector:

    def __init__(self, config: Config):
        self.config = config

    def iter_check_module_names(self) -> Iterable[str]:
        for fn in os.listdir(Path(checks.__file__).parent):
            if fn in ("__init__.py", "__pycache__"):
                continue
            else:
                yield fn.replace(".py", "")

    def import_check_module(self, module_name: str) -> ModuleType:
        import_path = f"debby.checks.{module_name}"
        return import_module(import_path)

    def iter_checks(self) -> Iterable[Check]:
        for module_name in self.iter_check_module_names():
            module = self.import_check_module(module_name)
            check_config = self.config.get_check_config(
                module_name, check_module=module
            )
            yield Check(module=module, config=check_config)

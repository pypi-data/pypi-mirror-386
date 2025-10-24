import inspect
from packaging.version import Version
from enum import Enum
from dataclasses import dataclass
from typing import Any, Iterable, Callable, TYPE_CHECKING
from types import ModuleType
from debby.config import CheckConfig


if TYPE_CHECKING:
    from .runner import RunStatus
    from .artifacts import Manifest


class CheckResultStatus(Enum):
    passing = "pass"
    failing = "fail"
    warning = "warn"
    error = "error"


@dataclass
class CheckResult:
    check_instance: "CheckInstance"
    status: CheckResultStatus


class CheckArgs:

    reserved_parameter_names = (
        "model",
        "source",
        "parents",
        "children",
        "ancestors",
        "descendants",
        "manifest",
        "tests",
    )

    def __init__(self, check: "Check"):
        self.check = check

    # TODO: some error handling here will be important for users of the framework
    # to alert them when they've misconfigured a check
    def resource_type(self) -> str:
        return next(iter(self.check.parameters))

    @property
    def custom_parameter_names(self):
        return [
            p for p in self.check.parameters if p not in self.reserved_parameter_names
        ]

    @property
    def custom_parameter_defaults(self):
        return [self.check.parameters[n].default for n in self.custom_parameter_names]

    @property
    def custom_parameter_annotations(self):
        return [
            self.check.parameters[n].annotation for n in self.custom_parameter_names
        ]


class Check:

    def __init__(self, module: ModuleType, config: CheckConfig):
        self.module = module
        self.config = config
        self.args = CheckArgs(check=self)

    @property
    def name(self):
        return self.module.__name__.split(".")[-1]

    @property
    def resource_type(self):
        return self.args.resource_type()

    @property
    def minimum_debby_version(self) -> Version:
        return Version(self.module.minimum_debby_version.lstrip("v"))

    @property
    def docs(self):
        return self.module.__doc__

    @property
    def description(self):
        return self.module.description

    @property
    def parameters(self):
        return inspect.signature(self.runner()).parameters

    def is_enabled_for(self, node: dict[str, Any]):
        if not self.config.enabled:
            return False
        elif node["resource_type"] != self.resource_type:
            return False
        elif node["name"] in self.config.skip:
            return False
        elif set(node.get("tags", [])).intersection(self.config.skip_tags):
            return False
        elif any(
            node["original_file_path"].startswith(p) for p in self.config.skip_paths
        ):
            return False
        else:
            return True

    def runner(self) -> Callable[..., Any]:
        _runner = getattr(self.module, "check")
        if not callable(_runner):
            raise ValueError(f"Unable to find valid 'check' method for {self.name}.")
        return _runner


class CheckInstanceArgs:
    def __init__(self, check_instance: "CheckInstance", manifest: "Manifest"):
        self.check_instance = check_instance
        self.manifest = manifest
        self._dict_cache = None

    def items(self) -> Iterable[tuple[str, Any]]:
        yield (self.check_instance.check.resource_type, self.check_instance.node)

        for argname, argval in self.iter_custom_args():
            if override := self.check_instance.check.config.param(argname):
                yield (argname, override)
            else:
                yield (argname, argval)

        if "children" in self.check_instance.check.parameters:
            yield ("children", self.children())
        if "parents" in self.check_instance.check.parameters:
            yield ("parents", self.parents())
        if "manifest" in self.check_instance.check.parameters:
            yield ("manifest", self.manifest)
        if "ancestors" in self.check_instance.check.parameters:
            yield ("ancestors", self.ancestors())
        if "descendants" in self.check_instance.check.parameters:
            yield ("descendants", self.descendants())
        if "tests" in self.check_instance.check.parameters:
            yield ("tests", self.tests())

    def iter_custom_args(self) -> Iterable[tuple[str, Any]]:
        for argname in self.check_instance.check.args.custom_parameter_names:
            yield (argname, self.check_instance.check.parameters[argname].default)

    def dict(self) -> dict[str, Any]:
        if self._dict_cache is None:
            self._dict_cache = dict(self.items())
        return self._dict_cache

    def __getitem__(self, key: str):
        return self.dict()[key]

    def __contains__(self, key: str):
        return key in self.dict()

    def tests(self):
        return self.manifest.get_tests(self.check_instance.node["unique_id"])

    def children(self):
        return self.manifest.get_children(self.check_instance.node["unique_id"])

    def parents(self):
        return self.manifest.get_parents(self.check_instance.node["unique_id"])

    def ancestors(self):
        return self.manifest.get_ancestors(self.check_instance.node["unique_id"])

    def descendants(self):
        return self.manifest.get_descendants(self.check_instance.node["unique_id"])


class CheckInstance:
    def __init__(self, check: Check, node: dict[str, Any], manifest: "Manifest"):
        self.check = check
        self.node = node
        self.args = CheckInstanceArgs(check_instance=self, manifest=manifest)

    def run(self, run_status: "RunStatus") -> CheckResult:
        runner = self.check.runner()
        args = self.args.dict()
        try:
            runner(**args)
            status = CheckResultStatus.passing
            run_status.passing += 1
        except AssertionError:
            status = CheckResultStatus.failing
            run_status.failing += 1
        except Exception:
            status = CheckResultStatus.error
            run_status.errors += 1
        return CheckResult(check_instance=self, status=status)

import os
import asyncio
from click import group, option, argument, pass_context, make_pass_decorator
from click import Context, Option
from pathlib import Path
from debby.collector import Collector
from debby.artifacts import Manifest
from debby.runner import Runner
from debby.config import Config


pass_config = make_pass_decorator(Config)


@group(no_args_is_help=True)
@option(
    "--config-path",
    "-c",
    default=os.path.join(os.getcwd(), ".debby", "config.toml"),
    type=Path,
    help="Path to a configuration file.",
    envvar="DEBBY_CONFIG_PATH",
)
@pass_context
def cli(ctx: Context, config_path: Path):
    """
    An extensible dbt linter.

    https://debbyapp.com/docs
    """

    if config_path.exists():
        config = Config.from_path(config_path)
    else:
        config = Config()
    ctx.obj = config


@cli.command(name="list")
@pass_config
def list_checks(config: Config):
    """
    List available checks
    """

    collector = Collector(config=config)
    for check in collector.iter_checks():
        print(check.name)


# TODO: currently the `model_path` arg is present just because pre-commit will pass
# a list of filenames when it runs. But we don't actually do anything with those model
# paths. We should eventually use them to filter the models that are checked. But there's
# two reasons this gets tricky:
# 1. What if the path is from a dbt project in a subdirectory? In that case the model path
#    will not align with the changed file path passed by pre-commit. So identifying which
#    model has actually changed is not directly straightforward.
# 2. What if we want to check multiple types of resources? Ie, how should we identify when
#    something like a macro has changed, to only test that resource?
@cli.command(name="run")
@option(
    "--artifacts-path",
    default=Path(os.getcwd()) / "target",
    type=Path,
    help="Path to a compiled dbt project's `target` directory.",
)
@argument("model-path", nargs=-1, type=Path)
@pass_config
def run_checks(config: Config, artifacts_path: Path, model_path: list[Path]):
    """
    Run checks against a dbt project.
    """

    manifest = Manifest.from_path(artifacts_path / "manifest.json")
    collector = Collector(config=config)
    runner = Runner(collector=collector, manifest=manifest)
    for _ in asyncio.run(runner.run()):
        pass

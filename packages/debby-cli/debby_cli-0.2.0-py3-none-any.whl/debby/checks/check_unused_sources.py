"""
This check identifies sources that are not being used directly by
any models. This indicates the source can be removed or disabled.
"""

minimum_debby_version = "v0.2.0"
description = "Identify unused sources"
enabled = False


def check(source: dict, children: list[dict]):
    child_models = [m for m in children if m["resource_type"] == "model"]
    assert len(child_models) != 0

"""
This check validates that a staging model depends on only a single source.

It's a best practice for staging models to have a one-to-one relationship with
their source.
"""

from typing import Any
from debby.helpers import is_staging_model


minimum_debby_version = "v0.2.0"
description = "Ensure a one-to-one relationship between sources and their staging model"


def check(model: dict, parents: list[dict]):
    if is_staging_model(model):
        upstream_models = [p for p in parents if p["resource_type"] == "model"]
        assert len(upstream_models) == 0

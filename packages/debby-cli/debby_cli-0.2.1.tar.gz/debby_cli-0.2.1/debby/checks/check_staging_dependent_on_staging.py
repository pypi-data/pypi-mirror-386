"""
This check validates that a staging model does not depend on any other staging models.
"""

from typing import Any
from debby.helpers import is_staging_model


minimum_debby_version = "v0.2.0"
description = "Ensure staging models depend only on sources"


def check(model: dict, parents: list[dict]):
    if is_staging_model(model):
        upstream_staging_models = [p for p in parents if is_staging_model(p)]
        assert not any(upstream_staging_models)

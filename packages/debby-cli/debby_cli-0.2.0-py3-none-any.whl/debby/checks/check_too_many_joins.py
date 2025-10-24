"""
This check identifies models with a large number of joins.
"""

from typing import Any


minimum_debby_version = "v0.2.0"
description = "Identify models that may potentially be too complex"
max_joined_models_description = "The maximum number of upstream models allowed"
enabled = False


def check(model: dict, parents: list[dict], max_joined_models: int = 7):
    assert len(parents) <= max_joined_models

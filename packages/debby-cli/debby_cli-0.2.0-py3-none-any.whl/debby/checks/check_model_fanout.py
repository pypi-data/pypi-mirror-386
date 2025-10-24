"""
This check validates that a model has a limited number of direct children.
"""

from typing import Any


minimum_debby_version = "v0.2.0"
description = "Limit the total number of models that depend on a model"
enabled = False
max_downstream_models_description = (
    "The maximum number of direct child models the model is allowed to have"
)


def check(model: dict, children: list[dict], max_downstream_models: int = 5):
    downstream_models = [c for c in children if c["resource_type"] == "model"]
    assert len(downstream_models) <= max_downstream_models

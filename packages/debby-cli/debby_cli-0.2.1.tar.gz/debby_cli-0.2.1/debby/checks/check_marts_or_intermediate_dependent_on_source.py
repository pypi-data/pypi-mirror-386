"""
This check identifies intermediate or mart models that are dependent on sources.

It's best practice for a source to be first referenced by a staging model.
"""

from debby.helpers import is_mart_model, is_intermediate_model


minimum_debby_version = "v0.2.0"
description = (
    "Ensure sources are not referenced directly by mart or intermediate models"
)
enabled = False


def check(model: dict, parents: list[dict]):
    if is_mart_model(model) or is_intermediate_model(model):
        sources = [p for p in parents if p["resource_type"] == "source"]
        assert len(sources) == 0

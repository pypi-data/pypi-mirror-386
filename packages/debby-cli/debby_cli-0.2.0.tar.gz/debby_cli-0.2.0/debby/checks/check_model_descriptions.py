"""
This check validates that a model has specified a description in its model config.
"""

from typing import Any

description = "Ensure all models include a description"
minimum_debby_version = "v0.1.0"
minimum_length_description = "The minimum length of the description"


def check(model: dict, minimum_length: int = 10):
    assert model["description"] is not None
    assert len(model["description"]) > minimum_length

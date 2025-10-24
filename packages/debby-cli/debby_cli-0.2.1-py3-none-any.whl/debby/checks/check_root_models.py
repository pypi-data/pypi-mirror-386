"""
This check identifies models that have no direct parents. This often means the model is
not using the `ref` function for referencing source data that it uses.

There are some cases where this is intentional and adding an exception for this check
makes sense. For example, a "calendar" model that generates a list of dates would not
directly use a source or another model. To disable this check for specific models, see
the documentation on [model configuration](../configuration.md)
"""

minimum_debby_version = "v0.2.0"
description = "Identify models not using the `ref` function"
enabled = False


def check(model: dict, parents: list[dict]):
    assert len(parents) > 0

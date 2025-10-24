"""
This check validates that a staging model does not use two sources.

The best practice for project structure is to have a 1:1 relationship between sources and
their staging models. This ensures that a single location is used for the initial transformations
of a raw source table, such as renaming and recasting fields from the source.
"""

minimum_debby_version = "v0.2.0"
description = "Ensure a one-to-one relationship between sources and their staging model"


def check(model: dict, parents: dict):
    direct_sources = [p for p in parents if p["resource_type"] == "source"]
    assert len(direct_sources) <= 1

"""
This check validates that a source is only used directly by a single model.

It's best practice to "wrap" each source with a single view that performs basic operations like renaming fields, casting data types, and other operations. Any other transformations related to operations like joining, filtering, or applying business logic should be left for further later in the pipeline.
"""

from typing import Any


minimum_debby_version = "v0.2.0"
description = "Ensure source models have a single location for renaming, recasting, etc"


def check(source: dict, children: list[dict]):
    child_models = [m["name"] for m in children if m["resource_type"] == "model"]
    assert len(child_models) < 2

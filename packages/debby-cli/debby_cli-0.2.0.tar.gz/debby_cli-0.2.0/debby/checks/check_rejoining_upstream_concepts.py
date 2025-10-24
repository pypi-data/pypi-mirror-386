"""
This check identifies unnecessary "loops" in the dag.
"""

from typing import Any
from debby.artifacts import Manifest


minimum_debby_version = "v0.2.0"
description = "Identify unecessary loops in the DAG"
enabled = False


def check(model: dict, parents: list[dict], manifest: Manifest):
    parent_node_ids = [p["unique_id"] for p in parents]
    grand_parent_node_ids = [
        gp["unique_id"] for p in parents for gp in manifest.get_parents(p["unique_id"])
    ]
    for p in parent_node_ids:
        if len(manifest.get_parents(p)) == 1:
            gp_id = manifest.get_parents(p)[0]["unique_id"]
            assert gp_id not in grand_parent_node_ids

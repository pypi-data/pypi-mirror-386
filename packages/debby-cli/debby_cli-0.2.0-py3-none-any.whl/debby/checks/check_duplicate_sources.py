"""
This check identifies instances where two different sources use the same raw database table.
"""

from typing import Any
from debby.artifacts import Manifest

description = "Ensure a raw table is referenced by only a single source"
enabled = False
minimum_debby_version = "v0.2.0"


def check(source: dict, manifest: Manifest):
    def get_compiled_source(source: dict):
        if source["database"]:
            return f"{source["database"]}.{source["schema"]}.{source["identifier"]}"
        else:
            return f"{source["schema"]}.{source["identifier"]}"

    compiled = get_compiled_source(source)

    for other in manifest.iter_sources():
        if other["unique_id"] == source["unique_id"]:
            continue
        assert not compiled == get_compiled_source(other)

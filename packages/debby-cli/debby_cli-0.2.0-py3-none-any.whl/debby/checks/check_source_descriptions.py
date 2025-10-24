"""
This check validates that a source has specified a description in its source config.
"""

from typing import Any


minimum_debby_version = "v0.2.0"
description = "Ensure all sources include a description"


def check(source: dict):
    assert source["source_description"] not in (None, "")

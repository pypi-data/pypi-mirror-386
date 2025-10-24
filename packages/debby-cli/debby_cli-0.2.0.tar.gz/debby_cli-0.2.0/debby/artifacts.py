from typing import Iterable
from functools import cache
import json
from pathlib import Path
from typing import Any


class Manifest:
    def __init__(self, data: dict[str, Any]):
        self.data = data
        self._nodes_cache = None

    @classmethod
    def from_path(cls, path: Path):
        with path.open() as fh:
            data = json.load(fh)
            return Manifest(data=data)

    def iter_models(self) -> Iterable[dict[str, Any]]:
        for node in self.data["nodes"].values():
            if node["resource_type"] == "model":
                yield node

    def iter_sources(self) -> Iterable[dict[str, Any]]:
        for node in self.nodes().values():
            if node["resource_type"] == "source":
                yield node

    # TODO: consolidate with `items` and `nodes` method
    def iter_nodes(self) -> Iterable[dict[str, Any]]:
        for node in self.data["nodes"].values():
            yield node
        for node in self.data["sources"].values():
            yield node

    def items(self) -> Iterable[tuple[str, Any]]:
        for node_id, node in self.data["nodes"].items():
            yield node_id, node
        for node_id, node in self.data["sources"].items():
            yield node_id, node

    def nodes(self) -> dict[str, Any]:
        if self._nodes_cache is None:
            self._nodes_cache = dict(self.items())
        return self._nodes_cache

    def get_node(self, node_id: str) -> dict[str, Any]:
        return self.nodes()[node_id]

    def get_tests(self, node_id: str) -> list[dict[str, Any]]:
        child_nodes = self.get_children(node_id)
        return [c for c in child_nodes if c["resource_type"] == "test"]

    @cache
    def get_ancestor_node_ids(self, node_id: str) -> set[str]:
        ancestor_ids: set[str] = set()

        def _collect_ancestors(current_node_id: str):
            if current_node_id in self.data["parent_map"]:
                parent_ids = self.data["parent_map"][current_node_id]
                for parent_id in parent_ids:
                    if parent_id not in ancestor_ids:  # Avoid cycles
                        ancestor_ids.add(parent_id)
                        _collect_ancestors(parent_id)

        _collect_ancestors(node_id)
        return ancestor_ids

    @cache
    def get_descendant_node_ids(self, node_id: str) -> set[str]:
        descendant_ds: set[str] = set()

        def _collect_descendants(current_node_id: str):
            if current_node_id in self.data["child_map"]:
                child_ids = self.data["child_map"][current_node_id]
                for child_id in child_ids:
                    if child_id not in descendant_ds:  # Avoid cycles
                        descendant_ds.add(child_id)
                        _collect_descendants(child_id)

        _collect_descendants(node_id)
        return descendant_ds

    def get_children(self, node_id: str) -> list[dict[str, Any]]:
        child_ids = self.data["child_map"][node_id]
        children = [self.nodes()[child_id] for child_id in child_ids]
        return children

    def get_parents(self, node_id: str) -> list[dict[str, Any]]:
        parent_ids = self.data["parent_map"][node_id]
        parents = [self.nodes()[parent_id] for parent_id in parent_ids]
        return parents

    def get_ancestors(self, node_id: str) -> list[dict[str, Any]]:
        ancestor_ids = self.get_ancestor_node_ids(node_id)
        ancestors = [self.nodes()[ancestor_id] for ancestor_id in ancestor_ids]
        return ancestors

    def get_descendants(self, node_id: str) -> list[dict[str, Any]]:
        descendant_ids = self.get_descendant_node_ids(node_id)
        descendants = [self.nodes()[descendant_id] for descendant_id in descendant_ids]
        return descendants

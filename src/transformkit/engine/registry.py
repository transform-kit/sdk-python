"""Node registry — maps node type strings to their executable definitions."""

from __future__ import annotations

from typing import Optional

from ..types import NodeDefinition


class NodeRegistry:
    """Registry for node definitions.

    Use :func:`create_default_registry` to get a pre-loaded registry.
    """

    def __init__(self) -> None:
        self._definitions: dict[str, NodeDefinition] = {}

    def register(self, node_definition: NodeDefinition) -> None:
        """Register a node definition. Overwrites any existing definition with the same type."""
        self._definitions[node_definition.type] = node_definition

    def get(self, type_: str) -> Optional[NodeDefinition]:
        """Look up a node definition by type."""
        return self._definitions.get(type_)

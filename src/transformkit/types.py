"""Core data types mirroring the TypeScript SDK."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol, Sequence


@dataclass
class Metadata:
    """File metadata carried through the pipeline."""

    extension: str
    """Without the dot (e.g. ``'png'``, ``'heic'``, ``'mp4'``)."""

    mime_type: str

    source_path: Optional[str] = None
    """Lets transports read from disk instead of serialising large buffers."""

    source_file_name: Optional[str] = None
    """Original queue filename. Preserved through transform nodes for output naming."""

    output_file_name: Optional[str] = None
    """Set by ``pipeline.output`` — final basename including extension."""


@dataclass
class ExecutionContext:
    """Context passed through the pipeline. Carries the file bytes and metadata."""

    file: bytes
    """Empty bytes when using ``convert_from_path`` on the first hop."""

    metadata: Metadata


@dataclass
class NodeResultContinue:
    status: str = field(default="continue", init=False)
    ctx: ExecutionContext


@dataclass
class NodeResultSkip:
    status: str = field(default="skip", init=False)


@dataclass
class NodeResultOutput:
    status: str = field(default="output", init=False)
    ctx: ExecutionContext


NodeResult = NodeResultContinue | NodeResultSkip | NodeResultOutput


@dataclass
class ConfigField:
    """A single config field value with optional UI metadata."""

    value: Any
    editable: bool
    options: Optional[Sequence[Any]] = None


class Transport(Protocol):
    """Abstracts the backend that performs actual file conversion."""

    async def convert(self, file: bytes, config: dict[str, Any]) -> bytes: ...

    async def convert_from_path(self, path: str, config: dict[str, Any]) -> bytes:
        """Optional path-based conversion. Default raises NotImplementedError."""
        ...


class NodeExecuteFn(Protocol):
    """Signature for a node's execute function."""

    async def __call__(
        self,
        ctx: ExecutionContext,
        config: dict[str, ConfigField],
        transport: Transport,
    ) -> NodeResult: ...


@dataclass
class NodeDefinition:
    """A node definition — the executable logic for a node type."""

    type: str
    execute: Callable[
        [ExecutionContext, dict[str, ConfigField], Transport],
        asyncio.coroutines,
    ]


@dataclass
class NodeInstance:
    """A node instance in a pipeline — references a definition type and holds config values."""

    id: str
    type: str
    config: Optional[dict[str, ConfigField]] = None


@dataclass
class Edge:
    """An edge connecting two nodes (source -> target)."""

    source: str
    target: str


@dataclass
class Pipeline:
    """A pipeline definition — a DAG of nodes connected by edges."""

    nodes: list[NodeInstance]
    edges: list[Edge]


@dataclass
class NodeCatalogEntry:
    """One built-in node type with category metadata for pickers.

    Labels are intentionally omitted. Hosts derive display text from
    ``sdk_type`` through their own i18n layer, keeping the catalog
    language-agnostic.
    """

    sdk_type: str
    category_id: str

"""Shared execute function for extension filter nodes."""

from __future__ import annotations

from ..types import (
    ConfigField,
    ExecutionContext,
    NodeDefinition,
    NodeResult,
    NodeResultContinue,
    NodeResultSkip,
    Transport,
)


async def _execute_extension_filter(
    ctx: ExecutionContext,
    config: dict[str, ConfigField],
    _transport: Transport,
) -> NodeResult:
    extension_field = config.get("extension")
    extension = extension_field.value if extension_field else None
    if not extension:
        return NodeResultContinue(ctx=ctx)

    ext = ctx.metadata.extension.lower()
    want = str(extension).lower()
    match = (ext in ("heic", "heif")) if want == "heic" else (ext == want)
    return NodeResultContinue(ctx=ctx) if match else NodeResultSkip()


def extension_filter_node(type_: str) -> NodeDefinition:
    """Create a filter node definition that passes or skips based on file extension."""
    return NodeDefinition(type=type_, execute=_execute_extension_filter)

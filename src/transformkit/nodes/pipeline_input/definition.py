"""Pipeline entry point: no-op passthrough."""

from __future__ import annotations

from ...types import (
    ConfigField,
    ExecutionContext,
    NodeDefinition,
    NodeResult,
    NodeResultContinue,
    Transport,
)


async def _execute(ctx: ExecutionContext, _config: dict[str, ConfigField], _transport: Transport) -> NodeResult:
    return NodeResultContinue(ctx=ctx)


pipeline_input = NodeDefinition(type="pipeline.input", execute=_execute)

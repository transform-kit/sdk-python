"""Terminal node: names the output file and collects the result."""

from __future__ import annotations

from copy import copy

from ...types import (
    ConfigField,
    ExecutionContext,
    NodeDefinition,
    NodeResult,
    NodeResultOutput,
    Transport,
)
from ...utils import normalize_ext
from .utils import stem_and_ext


async def _execute(ctx: ExecutionContext, config: dict[str, ConfigField], _transport: Transport) -> NodeResult:
    suffix_raw = config.get("nameSuffix")
    suffix = suffix_raw.value if suffix_raw and isinstance(suffix_raw.value, str) else ""
    trimmed_suffix = suffix.strip()

    source_name = ctx.metadata.source_file_name
    if not source_name or not source_name.strip():
        source_name = f"file.{ctx.metadata.extension}"
    else:
        import re

        source_name = re.sub(r"^.*[/\\]", "", source_name).strip()

    stem, source_ext_raw = stem_and_ext(source_name)
    source_ext = normalize_ext(source_ext_raw)
    out_ext = normalize_ext(ctx.metadata.extension or source_ext_raw or "bin")

    if trimmed_suffix == "":
        output_file_name = f"{stem}.{out_ext}"
        overwrite_source = source_ext != "" and source_ext == out_ext
    else:
        output_file_name = f"{stem}{trimmed_suffix}.{out_ext}"
        overwrite_source = False

    new_meta = copy(ctx.metadata)
    new_meta.output_file_name = output_file_name
    new_meta.overwrite_source = overwrite_source

    return NodeResultOutput(ctx=ExecutionContext(file=ctx.file, metadata=new_meta))


pipeline_output = NodeDefinition(type="pipeline.output", execute=_execute)

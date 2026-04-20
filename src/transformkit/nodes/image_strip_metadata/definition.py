"""image.strip-metadata node definition.

Strip EXIF/XMP/IPTC/tag metadata from an image buffer (ICC color profile
preserved). Passes through unchanged when ``enabled`` is ``False``. Otherwise
asks the transport to re-emit the current buffer with metadata stripped using
``operation: "strip-metadata"`` so transports can distinguish this cheap path
from a full re-encode.
"""

from __future__ import annotations

from ...types import (
    ConfigField,
    ExecutionContext,
    Metadata,
    NodeDefinition,
    NodeResult,
    NodeResultContinue,
    Transport,
)
from ...utils import is_editable


async def _execute(
    ctx: ExecutionContext,
    config: dict[str, ConfigField],
    transport: Transport,
) -> NodeResult:
    enabled_field = config.get("enabled")
    raw = enabled_field.value if enabled_field else True
    if isinstance(raw, bool):
        enabled = raw
    else:
        enabled = raw not in (False, 0, "0", "false", "False")

    if not enabled:
        return NodeResultContinue(ctx=ctx)

    payload: dict[str, object] = {
        "operation": "strip-metadata",
        "mediaType": "image",
        "inputExtension": ctx.metadata.extension,
        "editableFieldsResolved": {
            "enabled": {"value": enabled, "editable": is_editable(enabled_field)},
        },
    }

    buffer = await transport.convert(ctx.file, payload)

    metadata = Metadata(
        extension=ctx.metadata.extension,
        mime_type=ctx.metadata.mime_type,
        source_file_name=ctx.metadata.source_file_name,
    )
    return NodeResultContinue(ctx=ExecutionContext(file=buffer, metadata=metadata))


image_strip_metadata = NodeDefinition(type="image.strip-metadata", execute=_execute)

"""Converts a video to a different format via the transport."""

from __future__ import annotations

from ...mime import IMAGE_MIME, VIDEO_MIME
from ...transport.from_path import should_use_convert_from_path
from ...types import (
    ConfigField,
    ExecutionContext,
    Metadata,
    NodeDefinition,
    NodeResult,
    NodeResultContinue,
    Transport,
)


async def _execute(ctx: ExecutionContext, config: dict[str, ConfigField], transport: Transport) -> NodeResult:
    format_field = config.get("format")
    fmt_value = format_field.value if format_field else None
    if not fmt_value:
        return NodeResultContinue(ctx=ctx)

    quality_field = config.get("quality")
    quality = quality_field.value if quality_field and isinstance(quality_field.value, (int, float)) else 23

    payload: dict[str, object] = {
        "mediaType": "video",
        "format": fmt_value,
        "inputExtension": ctx.metadata.extension,
        "quality": quality,
    }

    source_path = ctx.metadata.source_path
    if should_use_convert_from_path(ctx.file, source_path, transport):
        buffer = await transport.convert_from_path(source_path, payload)  # type: ignore[arg-type]
    else:
        buffer = await transport.convert(ctx.file, payload)  # type: ignore[arg-type]

    extension = str(fmt_value).lower()
    return NodeResultContinue(
        ctx=ExecutionContext(
            file=buffer,
            metadata=Metadata(
                extension=extension,
                mime_type=VIDEO_MIME.get(extension, IMAGE_MIME.get(extension, f"video/{extension}")),
                source_file_name=ctx.metadata.source_file_name,
            ),
        )
    )


video_convert = NodeDefinition(type="video.convert", execute=_execute)

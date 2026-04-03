"""Converts an image to a different format via the transport."""

from __future__ import annotations

from ...mime import IMAGE_MIME
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
from ...utils import is_editable
from .utils import DEFAULT_PNG_COMPRESSION_SPEED, require_png_compression_speed


async def _execute(ctx: ExecutionContext, config: dict[str, ConfigField], transport: Transport) -> NodeResult:
    format_field = config.get("format")
    fmt_value = format_field.value if format_field else None
    if not fmt_value:
        return NodeResultContinue(ctx=ctx)

    quality_field = config.get("quality")
    quality = quality_field.value if quality_field and isinstance(quality_field.value, (int, float)) else 90

    fmt = str(fmt_value).lower()
    png_speed_field = config.get("pngCompressionSpeed")
    png_compression_speed = (
        require_png_compression_speed(png_speed_field.value if png_speed_field else None)
        if fmt == "png"
        else DEFAULT_PNG_COMPRESSION_SPEED
    )

    payload: dict[str, object] = {
        "format": fmt_value,
        "inputExtension": ctx.metadata.extension,
        "quality": quality,
        "pngCompressionSpeed": png_compression_speed,
        "editableFieldsResolved": {
            "format": {"value": fmt_value, "editable": is_editable(format_field)},
            "quality": {"value": quality, "editable": is_editable(quality_field)},
            **(
                {"pngCompressionSpeed": {"value": png_compression_speed, "editable": is_editable(png_speed_field)}}
                if fmt == "png"
                else {}
            ),
        },
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
                mime_type=IMAGE_MIME.get(extension, f"image/{extension}"),
                source_file_name=ctx.metadata.source_file_name,
            ),
        )
    )


image_convert = NodeDefinition(type="image.convert", execute=_execute)

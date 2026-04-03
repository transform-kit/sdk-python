"""Converts audio to a different format/bitrate via the transport."""

from __future__ import annotations

from ...mime import AUDIO_MIME
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

    bitrate_field = config.get("bitrate")
    bitrate = bitrate_field.value if bitrate_field and bitrate_field.value is not None else "192k"

    payload: dict[str, object] = {
        "mediaType": "audio",
        "format": fmt_value,
        "inputExtension": ctx.metadata.extension,
        "bitrate": bitrate,
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
                mime_type=AUDIO_MIME.get(extension, f"audio/{extension}"),
                source_file_name=ctx.metadata.source_file_name,
            ),
        )
    )


audio_convert = NodeDefinition(type="audio.convert", execute=_execute)

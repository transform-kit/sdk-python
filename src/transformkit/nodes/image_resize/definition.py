"""Resizes an image (percentage or pixel dimensions) via the transport."""

from __future__ import annotations

import math
from typing import Optional

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
from ...utils import is_editable, normalize_ext

_RESIZE_INTERNAL_QUALITY = 100
_RESIZE_INTERNAL_PNG_SPEED = "fast"


def _normalize_output_extension(ext: str) -> str:
    return normalize_ext(ext) or "png"


def _resize_output_extension(source_ext: str) -> str:
    e = _normalize_output_extension(source_ext)
    if e in ("heic", "heif"):
        return "png"
    return e


async def _execute(ctx: ExecutionContext, config: dict[str, ConfigField], transport: Transport) -> NodeResult:
    mode_raw = config.get("resizeMode")
    mode_val = mode_raw.value if mode_raw else ""
    mode_norm = str(mode_val).strip().lower() if mode_val else ""
    mode = "pixels" if mode_norm in ("pixels", "pixel") else "percentage"

    out_ext = _resize_output_extension(ctx.metadata.extension)
    quality = _RESIZE_INTERNAL_QUALITY
    png_compression_speed = _RESIZE_INTERNAL_PNG_SPEED

    resize_scale_percent: Optional[int] = None
    resize_width: Optional[int] = None
    resize_height: Optional[int] = None
    resize_fit: Optional[str] = None

    if mode == "percentage":
        p_field = config.get("percent")
        p = p_field.value if p_field else None
        try:
            p = float(p)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            p = None
        if p is None or not math.isfinite(p) or p < 1 or p > 100:
            return NodeResultContinue(ctx=ctx)
        resize_scale_percent = round(p)
    else:
        w_field = config.get("width")
        h_field = config.get("height")
        w_val = w_field.value if w_field else None
        h_val = h_field.value if h_field else None
        try:
            w = float(w_val)  # type: ignore[arg-type]
            w_ok = math.isfinite(w) and w > 0
        except (TypeError, ValueError):
            w_ok = False
            w = 0
        try:
            h = float(h_val)  # type: ignore[arg-type]
            h_ok = math.isfinite(h) and h > 0
        except (TypeError, ValueError):
            h_ok = False
            h = 0
        if not w_ok and not h_ok:
            return NodeResultContinue(ctx=ctx)
        if w_ok:
            resize_width = round(w)
        if h_ok:
            resize_height = round(h)
        fit_field = config.get("fit")
        if fit_field and isinstance(fit_field.value, str) and fit_field.value.strip():
            f = fit_field.value.strip().lower()
            if f in ("contain", "cover", "fill"):
                resize_fit = f

    editable_fields: dict[str, object] = {"resizeMode": {"value": mode, "editable": is_editable(mode_raw)}}
    if mode == "percentage":
        editable_fields["percent"] = {"value": resize_scale_percent, "editable": is_editable(config.get("percent"))}
    else:
        editable_fields["width"] = {"value": resize_width, "editable": is_editable(config.get("width"))}
        editable_fields["height"] = {"value": resize_height, "editable": is_editable(config.get("height"))}
        editable_fields["fit"] = {"value": resize_fit or "contain", "editable": is_editable(config.get("fit"))}

    payload: dict[str, object] = {
        "format": out_ext,
        "inputExtension": ctx.metadata.extension,
        "quality": quality,
        "pngCompressionSpeed": png_compression_speed,
        "resizeScalePercent": resize_scale_percent,
        "resizeWidth": resize_width,
        "resizeHeight": resize_height,
        "resizeFit": resize_fit,
        "editableFieldsResolved": editable_fields,
    }

    source_path = ctx.metadata.source_path
    if should_use_convert_from_path(ctx.file, source_path, transport):
        buffer = await transport.convert_from_path(source_path, payload)  # type: ignore[arg-type]
    else:
        buffer = await transport.convert(ctx.file, payload)  # type: ignore[arg-type]

    return NodeResultContinue(
        ctx=ExecutionContext(
            file=buffer,
            metadata=Metadata(
                extension=out_ext,
                mime_type=IMAGE_MIME.get(out_ext, f"image/{out_ext}"),
                source_file_name=ctx.metadata.source_file_name,
            ),
        )
    )


image_resize = NodeDefinition(type="image.resize", execute=_execute)

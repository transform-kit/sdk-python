"""Resizes a video (percentage or pixel dimensions) via the transport."""

from __future__ import annotations

import math
from typing import Optional

from ...mime import VIDEO_MIME
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
    mode_raw = config.get("resizeMode")
    mode_val = mode_raw.value if mode_raw else ""
    mode_norm = str(mode_val).strip().lower() if mode_val else ""
    mode = "pixels" if mode_norm in ("pixels", "pixel") else "percentage"

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

    ext = ctx.metadata.extension.lower()
    payload: dict[str, object] = {
        "mediaType": "video",
        "format": ext,
        "inputExtension": ext,
        "resizeScalePercent": resize_scale_percent,
        "resizeWidth": resize_width,
        "resizeHeight": resize_height,
        "resizeFit": resize_fit,
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
                extension=ext,
                mime_type=VIDEO_MIME.get(ext, f"video/{ext}"),
                source_file_name=ctx.metadata.source_file_name,
            ),
        )
    )


video_resize = NodeDefinition(type="video.resize", execute=_execute)

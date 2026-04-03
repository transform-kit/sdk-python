"""Canonical default configs for built-in node types, and config merging."""

from __future__ import annotations

from .mime import AUDIO_MIME, IMAGE_MIME, VIDEO_MIME
from .nodes.audio_convert.utils import BITRATE_OPTIONS, FORMAT_OPTIONS as AUDIO_FORMAT_OPTIONS
from .nodes.image_convert.utils import (
    DEFAULT_PNG_COMPRESSION_SPEED,
    FORMAT_OPTIONS as IMAGE_FORMAT_OPTIONS,
    PNG_COMPRESSION_SPEED_OPTIONS,
)
from .nodes.image_resize.utils import FIT_OPTIONS as IMAGE_FIT_OPTIONS, RESIZE_MODE_OPTIONS as IMAGE_RESIZE_MODE_OPTIONS
from .nodes.output_console.utils import DEFAULT_NAME_SUFFIX_FIELD
from .nodes.video_convert.utils import FORMAT_OPTIONS as VIDEO_FORMAT_OPTIONS
from .nodes.video_resize.utils import FIT_OPTIONS as VIDEO_FIT_OPTIONS, RESIZE_MODE_OPTIONS as VIDEO_RESIZE_MODE_OPTIONS
from .types import ConfigField, NodeCatalogEntry

NODE_CATALOG: tuple[NodeCatalogEntry, ...] = (
    NodeCatalogEntry(sdk_type="output.console", label="Output", category_id="common"),
    NodeCatalogEntry(sdk_type="image.filter", label="Filter", category_id="image"),
    NodeCatalogEntry(sdk_type="image.resize", label="Resize", category_id="image"),
    NodeCatalogEntry(sdk_type="image.convert", label="Convert", category_id="image"),
    NodeCatalogEntry(sdk_type="video.filter", label="Filter", category_id="video"),
    NodeCatalogEntry(sdk_type="video.resize", label="Resize", category_id="video"),
    NodeCatalogEntry(sdk_type="video.convert", label="Convert", category_id="video"),
    NodeCatalogEntry(sdk_type="audio.filter", label="Filter", category_id="audio"),
    NodeCatalogEntry(sdk_type="audio.convert", label="Convert", category_id="audio"),
)


def default_config_for_pipeline_node_type(sdk_type: str) -> dict[str, ConfigField]:
    """Returns the canonical default config for a given node type."""
    if sdk_type == "pipeline.input":
        return {}
    if sdk_type == "image.filter":
        return {"extension": ConfigField(value="png", editable=True, options=list(IMAGE_MIME.keys()), label="Extension")}
    if sdk_type == "video.filter":
        return {"extension": ConfigField(value="mp4", editable=True, options=list(VIDEO_MIME.keys()), label="Extension")}
    if sdk_type == "audio.filter":
        return {"extension": ConfigField(value="mp3", editable=True, options=list(AUDIO_MIME.keys()), label="Extension")}
    if sdk_type == "image.convert":
        return {
            "format": ConfigField(value="png", editable=True, options=IMAGE_FORMAT_OPTIONS, label="Format"),
            "quality": ConfigField(value=90, editable=True, label="Quality"),
            "pngCompressionSpeed": ConfigField(
                value=DEFAULT_PNG_COMPRESSION_SPEED,
                editable=True,
                options=list(PNG_COMPRESSION_SPEED_OPTIONS),
                label="PNG compression",
            ),
        }
    if sdk_type == "video.resize":
        return {
            "resizeMode": ConfigField(value="pixels", editable=True, options=list(VIDEO_RESIZE_MODE_OPTIONS), label="Resize mode"),
            "percent": ConfigField(value=50, editable=True, label="Percent (1\u2013100)"),
            "width": ConfigField(value=1920, editable=True, label="Width (px)"),
            "height": ConfigField(value=1080, editable=True, label="Height (px)"),
            "fit": ConfigField(value="contain", editable=True, options=list(VIDEO_FIT_OPTIONS), label="Fit (both dimensions)"),
        }
    if sdk_type == "video.convert":
        return {
            "format": ConfigField(value="mp4", editable=True, options=VIDEO_FORMAT_OPTIONS, label="Format"),
            "quality": ConfigField(value=23, editable=True, label="Quality (CRF)"),
        }
    if sdk_type == "audio.convert":
        return {
            "format": ConfigField(value="mp3", editable=True, options=AUDIO_FORMAT_OPTIONS, label="Format"),
            "bitrate": ConfigField(value="192k", editable=True, options=list(BITRATE_OPTIONS), label="Bitrate"),
        }
    if sdk_type == "image.resize":
        return {
            "resizeMode": ConfigField(value="percentage", editable=True, options=list(IMAGE_RESIZE_MODE_OPTIONS), label="Resize mode"),
            "percent": ConfigField(value=50, editable=True, label="Percent (1\u2013100)"),
            "width": ConfigField(value=1920, editable=True, label="Width (px)"),
            "height": ConfigField(value=1080, editable=True, label="Height (px)"),
            "fit": ConfigField(value="contain", editable=True, options=list(IMAGE_FIT_OPTIONS), label="Fit (both dimensions)"),
        }
    if sdk_type == "output.console":
        return {"nameSuffix": ConfigField(value=DEFAULT_NAME_SUFFIX_FIELD.value, editable=DEFAULT_NAME_SUFFIX_FIELD.editable, label=DEFAULT_NAME_SUFFIX_FIELD.label)}
    return {}


def _coerce_manifest_field(raw_field: object, base_field: ConfigField) -> ConfigField | None:
    """Normalize a manifest field: ``{value, editable, ...}`` or a bare primitive."""
    if isinstance(raw_field, ConfigField):
        return ConfigField(
            value=raw_field.value,
            editable=raw_field.editable if isinstance(raw_field.editable, bool) else base_field.editable,
            options=raw_field.options if raw_field.options is not None else base_field.options,
            label=raw_field.label if raw_field.label is not None else base_field.label,
        )
    if isinstance(raw_field, dict) and "value" in raw_field:
        editable = raw_field.get("editable", base_field.editable)
        if not isinstance(editable, bool):
            editable = base_field.editable
        options = raw_field.get("options", base_field.options)
        if not isinstance(options, (list, tuple)):
            options = base_field.options
        label = raw_field.get("label", base_field.label)
        if not isinstance(label, str):
            label = base_field.label
        return ConfigField(value=raw_field["value"], editable=editable, options=options, label=label)
    if isinstance(raw_field, (str, int, float, bool)):
        return ConfigField(value=raw_field, editable=base_field.editable, options=base_field.options, label=base_field.label)
    return None


def merge_pipeline_node_config(
    sdk_type: str,
    manifest_config: object,
) -> dict[str, ConfigField]:
    """Merge manifest ``config`` onto defaults so missing keys still render and execute."""
    defaults = default_config_for_pipeline_node_type(sdk_type)
    if not manifest_config or not isinstance(manifest_config, dict):
        return defaults
    raw: dict[str, object] = manifest_config
    out = dict(defaults)
    for key in defaults:
        base_field = defaults[key]
        if key in raw:
            coerced = _coerce_manifest_field(raw[key], base_field)
            if coerced is not None:
                out[key] = coerced
    return out

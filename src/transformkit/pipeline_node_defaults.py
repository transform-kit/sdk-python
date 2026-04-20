"""Canonical default configs for built-in node types, and config merging."""

from __future__ import annotations

from .mime import AUDIO_MIME, IMAGE_MIME, VIDEO_MIME
from .nodes.audio_convert.utils import BITRATE_OPTIONS, FORMAT_OPTIONS as AUDIO_FORMAT_OPTIONS
from .nodes.image_convert.utils import (
    DEFAULT_PNG_COMPRESSION_SPEED,
    FORMAT_OPTIONS as IMAGE_FORMAT_OPTIONS,
    PNG_COMPRESSION_SPEED_OPTIONS,
)
from .nodes.audio_strip_metadata.utils import (
    DEFAULT_STRIP_METADATA_ENABLED_FIELD as DEFAULT_AUDIO_STRIP_METADATA_ENABLED_FIELD,
)
from .nodes.image_resize.utils import FIT_OPTIONS as IMAGE_FIT_OPTIONS, RESIZE_MODE_OPTIONS as IMAGE_RESIZE_MODE_OPTIONS
from .nodes.image_strip_metadata.utils import (
    DEFAULT_STRIP_METADATA_ENABLED_FIELD as DEFAULT_IMAGE_STRIP_METADATA_ENABLED_FIELD,
)
from .nodes.pipeline_output.utils import DEFAULT_NAME_SUFFIX_FIELD
from .nodes.video_convert.utils import FORMAT_OPTIONS as VIDEO_FORMAT_OPTIONS
from .nodes.video_resize.utils import FIT_OPTIONS as VIDEO_FIT_OPTIONS, RESIZE_MODE_OPTIONS as VIDEO_RESIZE_MODE_OPTIONS
from .nodes.video_strip_metadata.utils import (
    DEFAULT_STRIP_METADATA_ENABLED_FIELD as DEFAULT_VIDEO_STRIP_METADATA_ENABLED_FIELD,
)
from .types import ConfigField, NodeCatalogEntry

NODE_CATALOG: tuple[NodeCatalogEntry, ...] = (
    NodeCatalogEntry(sdk_type="pipeline.input", category_id="common"),
    NodeCatalogEntry(sdk_type="pipeline.output", category_id="common"),
    NodeCatalogEntry(sdk_type="image.filter", category_id="image"),
    NodeCatalogEntry(sdk_type="image.resize", category_id="image"),
    NodeCatalogEntry(sdk_type="image.convert", category_id="image"),
    NodeCatalogEntry(sdk_type="image.strip-metadata", category_id="image"),
    NodeCatalogEntry(sdk_type="video.filter", category_id="video"),
    NodeCatalogEntry(sdk_type="video.resize", category_id="video"),
    NodeCatalogEntry(sdk_type="video.convert", category_id="video"),
    NodeCatalogEntry(sdk_type="video.strip-metadata", category_id="video"),
    NodeCatalogEntry(sdk_type="audio.filter", category_id="audio"),
    NodeCatalogEntry(sdk_type="audio.convert", category_id="audio"),
    NodeCatalogEntry(sdk_type="audio.strip-metadata", category_id="audio"),
)


def default_config_for_pipeline_node_type(sdk_type: str) -> dict[str, ConfigField]:
    """Returns the canonical default config for a given node type.

    Labels are intentionally omitted so pipelines stay language-agnostic. Hosts
    derive display text from the config key (or an i18n lookup keyed off node
    type + field key).
    """
    if sdk_type == "pipeline.input":
        return {}
    if sdk_type == "image.filter":
        return {"extension": ConfigField(value="png", editable=True, options=list(IMAGE_MIME.keys()))}
    if sdk_type == "video.filter":
        return {"extension": ConfigField(value="mp4", editable=True, options=list(VIDEO_MIME.keys()))}
    if sdk_type == "audio.filter":
        return {"extension": ConfigField(value="mp3", editable=True, options=list(AUDIO_MIME.keys()))}
    if sdk_type == "image.convert":
        return {
            "format": ConfigField(value="png", editable=True, options=IMAGE_FORMAT_OPTIONS),
            "quality": ConfigField(value=90, editable=True),
            "pngCompressionSpeed": ConfigField(
                value=DEFAULT_PNG_COMPRESSION_SPEED,
                editable=True,
                options=list(PNG_COMPRESSION_SPEED_OPTIONS),
            ),
        }
    if sdk_type == "video.resize":
        return {
            "resizeMode": ConfigField(value="pixels", editable=True, options=list(VIDEO_RESIZE_MODE_OPTIONS)),
            "percent": ConfigField(value=50, editable=True),
            "width": ConfigField(value=1920, editable=True),
            "height": ConfigField(value=1080, editable=True),
            "fit": ConfigField(value="contain", editable=True, options=list(VIDEO_FIT_OPTIONS)),
        }
    if sdk_type == "video.convert":
        return {
            "format": ConfigField(value="mp4", editable=True, options=VIDEO_FORMAT_OPTIONS),
            "quality": ConfigField(value=23, editable=True),
        }
    if sdk_type == "audio.convert":
        return {
            "format": ConfigField(value="mp3", editable=True, options=AUDIO_FORMAT_OPTIONS),
            "bitrate": ConfigField(value="192k", editable=True, options=list(BITRATE_OPTIONS)),
        }
    if sdk_type == "image.resize":
        return {
            "resizeMode": ConfigField(value="percentage", editable=True, options=list(IMAGE_RESIZE_MODE_OPTIONS)),
            "percent": ConfigField(value=50, editable=True),
            "width": ConfigField(value=1920, editable=True),
            "height": ConfigField(value=1080, editable=True),
            "fit": ConfigField(value="contain", editable=True, options=list(IMAGE_FIT_OPTIONS)),
        }
    if sdk_type == "pipeline.output":
        return {
            "nameSuffix": ConfigField(
                value=DEFAULT_NAME_SUFFIX_FIELD.value,
                editable=DEFAULT_NAME_SUFFIX_FIELD.editable,
            ),
        }
    if sdk_type == "image.strip-metadata":
        return {
            "enabled": ConfigField(
                value=DEFAULT_IMAGE_STRIP_METADATA_ENABLED_FIELD.value,
                editable=DEFAULT_IMAGE_STRIP_METADATA_ENABLED_FIELD.editable,
            ),
        }
    if sdk_type == "video.strip-metadata":
        return {
            "enabled": ConfigField(
                value=DEFAULT_VIDEO_STRIP_METADATA_ENABLED_FIELD.value,
                editable=DEFAULT_VIDEO_STRIP_METADATA_ENABLED_FIELD.editable,
            ),
        }
    if sdk_type == "audio.strip-metadata":
        return {
            "enabled": ConfigField(
                value=DEFAULT_AUDIO_STRIP_METADATA_ENABLED_FIELD.value,
                editable=DEFAULT_AUDIO_STRIP_METADATA_ENABLED_FIELD.editable,
            ),
        }
    return {}


def _coerce_manifest_field(raw_field: object, base_field: ConfigField) -> ConfigField | None:
    """Normalize a manifest field: ``{value, editable, ...}`` or a bare primitive.

    Labels are intentionally dropped. Pipelines stay language-agnostic; UIs map
    ``(nodeType, fieldKey)`` → display string through their own i18n layer.
    """
    if isinstance(raw_field, ConfigField):
        return ConfigField(
            value=raw_field.value,
            editable=raw_field.editable if isinstance(raw_field.editable, bool) else base_field.editable,
            options=raw_field.options if raw_field.options is not None else base_field.options,
        )
    if isinstance(raw_field, dict) and "value" in raw_field:
        editable = raw_field.get("editable", base_field.editable)
        if not isinstance(editable, bool):
            editable = base_field.editable
        options = raw_field.get("options", base_field.options)
        if not isinstance(options, (list, tuple)):
            options = base_field.options
        return ConfigField(value=raw_field["value"], editable=editable, options=options)
    if isinstance(raw_field, (str, int, float, bool)):
        return ConfigField(value=raw_field, editable=base_field.editable, options=base_field.options)
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

"""Built-in node definitions and default registry factory."""

from __future__ import annotations

from ..engine.registry import NodeRegistry
from .audio_convert.definition import audio_convert
from .audio_filter.definition import audio_filter
from .audio_strip_metadata.definition import audio_strip_metadata
from .image_convert.definition import image_convert
from .image_filter.definition import image_filter
from .image_resize.definition import image_resize
from .image_strip_metadata.definition import image_strip_metadata
from .pipeline_input.definition import pipeline_input
from .pipeline_output.definition import pipeline_output
from .video_convert.definition import video_convert
from .video_filter.definition import video_filter
from .video_resize.definition import video_resize
from .video_strip_metadata.definition import video_strip_metadata


def create_default_registry() -> NodeRegistry:
    """Create a registry with all built-in nodes registered."""
    registry = NodeRegistry()
    registry.register(pipeline_input)
    registry.register(image_filter)
    registry.register(video_filter)
    registry.register(audio_filter)
    registry.register(image_convert)
    registry.register(image_resize)
    registry.register(image_strip_metadata)
    registry.register(video_convert)
    registry.register(video_resize)
    registry.register(video_strip_metadata)
    registry.register(audio_convert)
    registry.register(audio_strip_metadata)
    registry.register(pipeline_output)
    return registry

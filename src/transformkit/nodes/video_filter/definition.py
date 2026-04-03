"""Passes videos matching the configured extension, skips others."""

from ..filter_common import extension_filter_node

video_filter = extension_filter_node("video.filter")

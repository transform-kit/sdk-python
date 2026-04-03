"""Passes audio files matching the configured extension, skips others."""

from ..filter_common import extension_filter_node

audio_filter = extension_filter_node("audio.filter")

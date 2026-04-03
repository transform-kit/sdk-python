"""Utilities for the audio.convert node."""

from ...mime import AUDIO_MIME

FORMAT_OPTIONS = list(AUDIO_MIME.keys())

BITRATE_OPTIONS = ("64k", "128k", "192k", "256k", "320k")

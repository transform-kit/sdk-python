"""Utilities for the image.convert node."""

from __future__ import annotations

from typing import Optional

from ...mime import IMAGE_MIME

_FORMAT_ALIASES = {"jpeg", "heif", "tif"}

FORMAT_OPTIONS = [k for k in IMAGE_MIME if k not in _FORMAT_ALIASES]

PNG_COMPRESSION_SPEED_OPTIONS = ("fast", "medium", "slow")

DEFAULT_PNG_COMPRESSION_SPEED = "fast"


def parse_png_compression_speed(value: object) -> Optional[str]:
    """Parse a raw value into a valid compression speed, or ``None``."""
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    return v if v in PNG_COMPRESSION_SPEED_OPTIONS else None


def require_png_compression_speed(value: object) -> str:
    """Parse and require a valid compression speed — raises if invalid."""
    v = parse_png_compression_speed(value)
    if v is None:
        raise ValueError(
            'image.convert requires config.pngCompressionSpeed.value to be "fast", "medium", or "slow".'
        )
    return v

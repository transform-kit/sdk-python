"""Shared utility functions."""

from __future__ import annotations

import asyncio
import re
from typing import Optional

from .types import ConfigField


def is_editable(field: Optional[ConfigField]) -> bool:
    """Returns ``True`` when a config field is marked as user-editable."""
    return field is not None and field.editable is True


def normalize_ext(ext: str) -> str:
    """Normalize a file extension: strip leading dot, lowercase, resolve aliases."""
    e = re.sub(r"^\.", "", ext.lower())
    if e == "jpeg":
        return "jpg"
    return e


async def next_tick() -> None:
    """Yield to the event loop."""
    await asyncio.sleep(0)

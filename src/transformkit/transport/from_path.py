"""Determine whether the transport should use convert_from_path."""

from __future__ import annotations

from typing import Any


def should_use_convert_from_path(
    file: bytes,
    source_path: str | None,
    transport: Any,
) -> bool:
    """Only returns ``True`` for the initial queued file (empty buffer + source_path)."""
    return (
        len(file) == 0
        and isinstance(source_path, str)
        and len(source_path) > 0
        and callable(getattr(transport, "convert_from_path", None))
    )

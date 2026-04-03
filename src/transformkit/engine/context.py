"""Create execution contexts from file bytes and extensions."""

from __future__ import annotations

from typing import Optional

from ..mime import mime_from_extension
from ..types import ExecutionContext, Metadata


def create_context(
    file: bytes,
    extension: str,
    mime_type: Optional[str] = None,
) -> ExecutionContext:
    """Create an :class:`ExecutionContext` from bytes and a file extension.

    Automatically resolves the MIME type from the extension for known formats.
    """
    resolved_mime = mime_type or mime_from_extension(extension) or "application/octet-stream"
    return ExecutionContext(
        file=file,
        metadata=Metadata(extension=extension, mime_type=resolved_mime),
    )

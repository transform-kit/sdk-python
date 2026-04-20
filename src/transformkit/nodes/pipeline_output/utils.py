"""Utilities for the pipeline.output node."""

from __future__ import annotations

from ...types import ConfigField


DEFAULT_NAME_SUFFIX_FIELD = ConfigField(value="", editable=True)


def stem_and_ext(file_name: str) -> tuple[str, str]:
    """Extract stem and last extension from a filename.

    Returns:
        ``(stem, ext)`` — e.g. ``("a.b", "png")``.
    """
    import re

    clean = re.sub(r"^.*[/\\]", "", file_name).strip()
    i = clean.rfind(".")
    if i <= 0 or i == len(clean) - 1:
        return (clean or "file", "")
    return (clean[:i], clean[i + 1 :])

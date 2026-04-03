"""Extension <-> MIME mapping for all supported media formats."""

from __future__ import annotations

from typing import Optional

IMAGE_MIME: dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "gif": "image/gif",
    "heic": "image/heic",
    "heif": "image/heif",
    "avif": "image/avif",
    "tiff": "image/tiff",
    "tif": "image/tiff",
}

VIDEO_MIME: dict[str, str] = {
    "mp4": "video/mp4",
    "avi": "video/x-msvideo",
    "mkv": "video/x-matroska",
    "webm": "video/webm",
    "mov": "video/quicktime",
    "wmv": "video/x-ms-wmv",
    "mpeg": "video/mpeg",
    "flv": "video/x-flv",
}

AUDIO_MIME: dict[str, str] = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "aac": "audio/aac",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
    "aiff": "audio/aiff",
}

ALL_MIME: dict[str, str] = {**IMAGE_MIME, **VIDEO_MIME, **AUDIO_MIME}


def mime_from_extension(ext: str) -> Optional[str]:
    """Look up a MIME type by file extension across all media types."""
    return ALL_MIME.get(ext.lower())


def _build_canonical_reverse() -> dict[str, str]:
    rev: dict[str, str] = {}
    for ext, mime in ALL_MIME.items():
        if mime not in rev:
            rev[mime] = ext
    rev["image/jpeg"] = "jpg"
    rev["image/tiff"] = "tiff"
    rev["image/heic"] = "heic"
    return rev


_CANONICAL_REVERSE = _build_canonical_reverse()


def extension_from_mime(mime: str) -> str:
    """Reverse lookup: MIME string -> file extension. Returns ``'bin'`` if unknown."""
    return _CANONICAL_REVERSE.get(mime.lower(), "bin")


def accept_string(category: str) -> str:
    """Build an HTML ``<input accept="...">`` string from a MIME map."""
    if category == "image":
        m = IMAGE_MIME
    elif category == "video":
        m = VIDEO_MIME
    elif category == "audio":
        m = AUDIO_MIME
    else:
        raise ValueError(f"Unknown category: {category}")
    extensions = [f".{ext}" for ext in m]
    return ",".join([f"{category}/*", *extensions])

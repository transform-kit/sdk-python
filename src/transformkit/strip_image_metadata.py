"""Bytewise lossless metadata stripping for JPEG and PNG.

The transports used to re-encode images through external tools to drop metadata.
That produces visible quality loss on JPEG (DCT round-trip) and needlessly
re-deflates PNG. This module walks the container structure and removes only
metadata segments, leaving the compressed pixel data byte-identical.

What is stripped:
- JPEG: APP1 (EXIF/XMP), APP13 (IPTC/Photoshop), other APPn (vendor metadata),
  COM (comments). APP0 (JFIF) and APP2 ICC_PROFILE are preserved. Non-ICC
  APP2 payloads (FlashPix, MPF) are dropped.
- PNG: tEXt, iTXt, zTXt, eXIf, tIME. All critical chunks and color/profile
  chunks (IHDR, PLTE, IDAT, IEND, iCCP, cHRM, gAMA, sRGB, sBIT, tRNS, …)
  are preserved.

ICC color profile is always preserved on both formats.
"""
from __future__ import annotations

from typing import Literal

StripSupportedExtension = Literal["jpg", "jpeg", "png"]


def is_strip_supported_extension(ext: str) -> bool:
    """Return True if *ext* is a format supported by :func:`strip_image_metadata_lossless`."""
    e = ext.lower().lstrip(".")
    return e in ("jpg", "jpeg", "png")


def strip_image_metadata_lossless(data: bytes | bytearray, ext: str) -> bytes:
    """Strip metadata from JPEG or PNG bytes without re-encoding.

    :param data: Raw image bytes.
    :param ext: File extension with or without a leading dot (e.g. ``"jpg"`` or ``".png"``).
    :returns: Cleaned image bytes with pixel data byte-identical to the input.
    :raises ValueError: When the buffer is malformed or the extension is not supported.
    """
    e = ext.lower().lstrip(".")
    if e in ("jpg", "jpeg"):
        return _strip_jpeg_metadata(bytes(data))
    if e == "png":
        return _strip_png_metadata(bytes(data))
    raise ValueError(
        f'Lossless metadata stripping supports JPEG and PNG only; got ".{e}". '
        "Add an image.convert node upstream to normalise the format first."
    )


# ── JPEG ─────────────────────────────────────────────────────────────────────

_ICC_PROFILE_SIG = b"ICC_PROFILE\x00"


def _strip_jpeg_metadata(src: bytes) -> bytes:
    if len(src) < 4 or src[0] != 0xFF or src[1] != 0xD8:
        raise ValueError("Invalid JPEG: missing SOI marker (FFD8)")

    parts: list[bytes] = [src[:2]]
    i = 2

    while i < len(src):
        if src[i] != 0xFF:
            raise ValueError(
                f"Invalid JPEG: expected marker at offset {i}, got 0x{src[i]:02x}"
            )
        while i < len(src) and src[i] == 0xFF:
            i += 1
        if i >= len(src):
            break
        marker = src[i]
        i += 1

        if marker == 0x00:
            continue
        if marker == 0xD9:
            parts.append(b"\xFF\xD9")
            return b"".join(parts)
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            parts.append(bytes([0xFF, marker]))
            continue

        if i + 1 >= len(src):
            raise ValueError("Truncated JPEG segment length")
        seg_len = (src[i] << 8) | src[i + 1]
        if seg_len < 2:
            raise ValueError(f"Invalid JPEG segment length {seg_len}")
        seg_start = i - 2
        payload_start = i + 2
        seg_end = i + seg_len
        if seg_end > len(src):
            raise ValueError("Truncated JPEG segment payload")

        if marker == 0xDA:  # SOS — keep header then copy entropy-coded data verbatim
            parts.append(src[seg_start:seg_end])
            k = seg_end
            ecs_start = k
            while k < len(src):
                if src[k] == 0xFF:
                    if k + 1 >= len(src):
                        break
                    nxt = src[k + 1]
                    if nxt == 0x00 or 0xD0 <= nxt <= 0xD7:
                        k += 2
                        continue
                    break
                k += 1
            parts.append(src[ecs_start:k])
            i = k
            continue

        if _should_keep_jpeg_segment(marker, src, payload_start, seg_end):
            parts.append(src[seg_start:seg_end])
        i = seg_end

    return b"".join(parts)


def _should_keep_jpeg_segment(
    marker: int, src: bytes, payload_start: int, payload_end: int
) -> bool:
    if marker == 0xE0:  # APP0 JFIF/JFXX
        return True
    if marker == 0xE2:  # APP2 — keep only ICC_PROFILE
        if payload_end - payload_start < len(_ICC_PROFILE_SIG):
            return False
        return src[payload_start : payload_start + len(_ICC_PROFILE_SIG)] == _ICC_PROFILE_SIG
    if 0xE1 <= marker <= 0xEF:  # APP1..APP15 (minus APP0/APP2 handled above)
        return False
    if marker == 0xFE:  # COM
        return False
    return True  # DQT, DHT, DRI, SOFx, DNL, etc.


# ── PNG ──────────────────────────────────────────────────────────────────────

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_STRIP = frozenset({"tEXt", "iTXt", "zTXt", "eXIf", "tIME"})


def _strip_png_metadata(src: bytes) -> bytes:
    if len(src) < 8:
        raise ValueError("Invalid PNG: too short")
    if src[:8] != _PNG_SIGNATURE:
        raise ValueError("Invalid PNG: bad signature")

    parts: list[bytes] = [src[:8]]
    i = 8

    while i < len(src):
        if i + 12 > len(src):
            raise ValueError("Truncated PNG chunk header")
        chunk_len = int.from_bytes(src[i : i + 4], "big")
        chunk_type = src[i + 4 : i + 8].decode("ascii")
        chunk_end = i + 12 + chunk_len
        if chunk_end > len(src):
            raise ValueError(f'Truncated PNG chunk "{chunk_type}"')

        if chunk_type not in _PNG_STRIP:
            parts.append(src[i:chunk_end])

        if chunk_type == "IEND":
            break
        i = chunk_end

    return b"".join(parts)

"""Resolve the pipeline endpoint URL from a base API origin."""

from __future__ import annotations

from urllib.parse import urlparse


def resolve_pipeline_url(base_url: str) -> str:
    """Resolve the full pipeline endpoint URL.

    If the pathname already ends with ``/v1``, appends ``/pipeline``.
    Otherwise appends ``/v1/pipeline``.

    Raises:
        ValueError: If *base_url* is not an absolute URL.
    """
    b = base_url.strip().rstrip("/")
    if not b.startswith("http://") and not b.startswith("https://"):
        raise ValueError("base_url must be an absolute URL (e.g. http://localhost:3002).")

    parsed = urlparse(b)
    path = parsed.path.rstrip("/")
    origin = f"{parsed.scheme}://{parsed.netloc}"

    if path.endswith("/v1"):
        return f"{origin}{path}/pipeline"
    return f"{origin}/v1/pipeline"

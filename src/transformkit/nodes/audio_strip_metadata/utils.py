"""Defaults for the ``audio.strip-metadata`` node.

When ``enabled`` is ``True`` (default), the node asks the transport to emit the
buffer with ID3/container/tag metadata removed via lossless stream copy. When
``False``, the node is a no-op passthrough — useful for A/B testing without
deleting and re-adding the node.
"""

from __future__ import annotations

from ...types import ConfigField


DEFAULT_STRIP_METADATA_ENABLED_FIELD = ConfigField(value=True, editable=True)

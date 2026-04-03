"""No-op transport for testing. Returns the input buffer unchanged."""

from __future__ import annotations

import asyncio
from typing import Any

from ..types import Transport


class MockTransport:
    """Pass-through transport with a simulated async delay."""

    def __init__(self, delay_ms: float = 10) -> None:
        self._delay = delay_ms / 1000.0

    async def convert(self, file: bytes, config: dict[str, Any]) -> bytes:
        await asyncio.sleep(self._delay)
        return bytes(file)


def create_mock_transport(delay_ms: float = 10) -> Transport:
    """Create a no-op transport for testing."""
    return MockTransport(delay_ms)  # type: ignore[return-value]

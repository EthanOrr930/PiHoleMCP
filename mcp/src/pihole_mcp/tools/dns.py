"""DNS blocking control tools."""

from __future__ import annotations

from fastmcp import FastMCP

from pihole_mcp.server import get_client
from pihole_mcp.util.validators import cap_duration


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_blocking_status() -> dict:
        """Return current Pi-hole blocking status and any active disable timer."""
        return await get_client().get_blocking_status()

    @mcp.tool
    async def set_blocking(
        enabled: bool,
        duration_seconds: int | None = None,
        confirm: bool = False,
    ) -> dict:
        """Enable or disable DNS-level ad blocking.

        Disabling REQUIRES duration_seconds (1..86400) so blocking cannot be
        turned off forever by accident. Requires confirm=True.
        """
        if not confirm:
            raise ValueError("Set confirm=True to change Pi-hole's blocking state.")
        if not enabled and duration_seconds is None:
            raise ValueError("duration_seconds is required when disabling blocking (max 86400).")
        timer = cap_duration(duration_seconds, 86400) if duration_seconds is not None else None
        return await get_client().set_blocking(blocking=enabled, timer=timer)

    @mcp.tool
    async def pause_blocking(duration_seconds: int) -> dict:
        """Convenience: disable blocking for N seconds (10..86400)."""
        if duration_seconds < 10 or duration_seconds > 86400:
            raise ValueError("duration_seconds must be between 10 and 86400.")
        return await get_client().set_blocking(blocking=False, timer=duration_seconds)

"""Pi-hole component log tail tools."""

from __future__ import annotations

from fastmcp import FastMCP

from pihole_mcp.server import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def tail_log_dnsmasq(next_id: int | None = None) -> dict:
        """Tail the dnsmasq (DNS) log. Pass `next_id` from prior call to resume."""
        return await get_client().logs_dnsmasq(next_id=next_id)

    @mcp.tool
    async def tail_log_ftl(next_id: int | None = None) -> dict:
        """Tail the FTL daemon log."""
        return await get_client().logs_ftl(next_id=next_id)

    @mcp.tool
    async def tail_log_webserver(next_id: int | None = None) -> dict:
        """Tail Pi-hole's embedded webserver log."""
        return await get_client().logs_webserver(next_id=next_id)

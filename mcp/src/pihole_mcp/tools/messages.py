"""Pi-hole diagnostic messages tools."""

from __future__ import annotations

from fastmcp import FastMCP

from pihole_mcp.server import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_messages() -> dict:
        """All current diagnostic messages from FTL (warnings, errors, info)."""
        return await get_client().info_messages()

    @mcp.tool
    async def get_messages_count() -> dict:
        """Just the count of current messages (cheap)."""
        return await get_client().info_messages_count()

    @mcp.tool
    async def delete_message(message_id: int, confirm: bool = False) -> dict:
        """Dismiss a single diagnostic message by id."""
        if not confirm:
            raise ValueError("Set confirm=True to delete the message.")
        await get_client().delete_info_message(message_id)
        return {"deleted_id": message_id}

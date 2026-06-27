"""Group management tools (per-device targeting buckets)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from pihole_mcp.server import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def list_groups() -> dict:
        """List all configured groups + their enabled/comment fields."""
        return await get_client().list_groups()

    @mcp.tool
    async def get_group(name: str) -> dict:
        """Look up a single group by name."""
        return await get_client().get_group(name)

    @mcp.tool
    async def create_group(name: str, comment: str = "", enabled: bool = True) -> dict:
        """Create a new group."""
        return await get_client().create_group(name=name, comment=comment or None, enabled=enabled)

    @mcp.tool
    async def update_group(
        name: str,
        new_name: str | None = None,
        comment: str | None = None,
        enabled: bool | None = None,
    ) -> dict:
        """Rename, edit comment, or toggle enabled on an existing group."""
        fields: dict[str, Any] = {}
        if new_name is not None:
            fields["name"] = new_name
        if comment is not None:
            fields["comment"] = comment
        if enabled is not None:
            fields["enabled"] = enabled
        return await get_client().update_group(name, **fields)

    @mcp.tool
    async def toggle_group(name: str, enabled: bool) -> dict:
        """Enable or disable a group (affects every rule scoped to it)."""
        return await get_client().update_group(name, enabled=enabled)

    @mcp.tool
    async def delete_group(name: str, confirm: bool = False) -> dict:
        """Delete a group. Requires confirm=True."""
        if not confirm:
            raise ValueError("Set confirm=True to delete the group.")
        await get_client().delete_group(name)
        return {"deleted": name}

    @mcp.tool
    async def batch_delete_groups(names: list[str], confirm: bool = False) -> dict:
        """Delete multiple groups at once. Requires confirm=True."""
        if not confirm:
            raise ValueError("Set confirm=True to batch-delete groups.")
        await get_client().batch_delete_groups(names)
        return {"deleted": names}

"""Adlist (blocklist/allowlist source URL) management tools."""

from __future__ import annotations

from typing import Any, Literal

from fastmcp import FastMCP

from pihole_mcp.server import get_client
from pihole_mcp.util.validators import is_http_url

ListType = Literal["block", "allow"]


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def list_adlists(
        type: ListType | None = None,
        cursor: int | None = None,
        limit: int | None = None,
    ) -> dict:
        """List all configured adlists, optionally filtered by type."""
        return await get_client().list_adlists(type=type, cursor=cursor, limit=limit)

    @mcp.tool
    async def get_adlist(url: str) -> dict:
        """Look up an adlist by its source URL."""
        return await get_client().get_adlist(url)

    @mcp.tool
    async def add_adlist(
        url: str,
        type: ListType = "block",
        groups: list[int] | None = None,
        comment: str = "",
        enabled: bool = True,
    ) -> dict:
        """Subscribe to a new adlist. URL must be http(s). Does NOT auto-run gravity."""
        if not is_http_url(url):
            raise ValueError(f"{url!r} is not a valid http(s) URL.")
        return await get_client().create_adlist(
            address=url, type=type, comment=comment or None, groups=groups, enabled=enabled,
        )

    @mcp.tool
    async def update_adlist(
        url: str,
        new_address: str | None = None,
        comment: str | None = None,
        groups: list[int] | None = None,
        enabled: bool | None = None,
        type: ListType | None = None,
    ) -> dict:
        """Update fields on an existing adlist."""
        fields: dict[str, Any] = {}
        if new_address is not None:
            if not is_http_url(new_address):
                raise ValueError(f"{new_address!r} is not a valid http(s) URL.")
            fields["address"] = new_address
        if comment is not None:
            fields["comment"] = comment
        if groups is not None:
            fields["groups"] = groups
        if enabled is not None:
            fields["enabled"] = enabled
        if type is not None:
            fields["type"] = type
        return await get_client().update_adlist(url, **fields)

    @mcp.tool
    async def toggle_adlist(url: str, enabled: bool, type: ListType = "block") -> dict:
        """Enable or disable an adlist without removing it."""
        return await get_client().update_adlist(url, enabled=enabled, type=type)

    @mcp.tool
    async def remove_adlist(url: str, type: ListType = "block", confirm: bool = False) -> dict:
        """Remove an adlist subscription. Requires confirm=True."""
        if not confirm:
            raise ValueError("Set confirm=True to remove the adlist.")
        await get_client().delete_adlist(url, type_=type)
        return {"deleted": {"url": url, "type": type}}

    @mcp.tool
    async def batch_remove_adlists(items: list[dict], confirm: bool = False) -> dict:
        """Bulk-remove adlists. items=[{url,type}], requires confirm=True."""
        if not confirm:
            raise ValueError("Set confirm=True to batch-delete adlists.")
        normalized = []
        for it in items:
            if "url" not in it and "address" not in it and "item" not in it:
                raise ValueError("Each item needs url (or address/item).")
            normalized.append({"item": it.get("url") or it.get("address") or it["item"], "type": it.get("type", "block")})
        await get_client().batch_delete_adlists(normalized)
        return {"deleted": normalized}

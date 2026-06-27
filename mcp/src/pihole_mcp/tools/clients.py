"""Client (device) management tools."""

from __future__ import annotations

import re
from typing import Any

from fastmcp import FastMCP

from pihole_mcp.server import get_client
from pihole_mcp.util.validators import normalize_mac

_MAC_LIKE = re.compile(r"^[0-9A-Fa-f]{2}([:-][0-9A-Fa-f]{2}){5}$|^[0-9A-Fa-f]{12}$")


def _normalize_identifier(identifier: str) -> str:
    if _MAC_LIKE.match(identifier.strip()):
        return normalize_mac(identifier)
    return identifier.strip()


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def list_clients() -> dict:
        """List configured clients with their group memberships."""
        return await get_client().list_clients()

    @mcp.tool
    async def list_unconfigured_clients() -> dict:
        """Clients FTL has seen but that are not assigned to any group."""
        return await get_client().get_client_suggestions()

    @mcp.tool
    async def get_client_detail(client: str) -> dict:
        """Look up a configured client by IP/CIDR/MAC/hostname/:interface."""
        return await get_client().get_client(_normalize_identifier(client))

    @mcp.tool
    async def add_client(
        identifier: str,
        groups: list[int] | None = None,
        comment: str = "",
    ) -> dict:
        """Register a client. Identifier may be IP, CIDR, MAC, hostname, or :interface."""
        return await get_client().add_client(
            client=_normalize_identifier(identifier), comment=comment or None, groups=groups,
        )

    @mcp.tool
    async def update_client(
        client: str,
        new_identifier: str | None = None,
        comment: str | None = None,
        groups: list[int] | None = None,
    ) -> dict:
        """Update a client's identifier, comment, or group memberships."""
        fields: dict[str, Any] = {}
        if new_identifier is not None:
            fields["client"] = _normalize_identifier(new_identifier)
        if comment is not None:
            fields["comment"] = comment
        if groups is not None:
            fields["groups"] = groups
        return await get_client().update_client(_normalize_identifier(client), **fields)

    @mcp.tool
    async def remove_client(client: str, confirm: bool = False) -> dict:
        """Delete a client configuration. Requires confirm=True."""
        if not confirm:
            raise ValueError("Set confirm=True to delete the client.")
        await get_client().delete_client(_normalize_identifier(client))
        return {"deleted": client}

    @mcp.tool
    async def batch_remove_clients(clients: list[str], confirm: bool = False) -> dict:
        """Bulk-remove clients by identifier. Requires confirm=True."""
        if not confirm:
            raise ValueError("Set confirm=True to batch-delete clients.")
        normalized = [_normalize_identifier(c) for c in clients]
        await get_client().batch_delete_clients(normalized)
        return {"deleted": normalized}

"""DHCP lease tools."""

from __future__ import annotations

from fastmcp import FastMCP

from pihole_mcp.server import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def list_dhcp_leases() -> dict:
        """All active DHCP leases (only meaningful if Pi-hole DHCP server is enabled)."""
        return await get_client().dhcp_leases()

    @mcp.tool
    async def revoke_dhcp_lease(ip: str, confirm: bool = False) -> dict:
        """Revoke a single lease by IP. Requires confirm=True."""
        if not confirm:
            raise ValueError("Set confirm=True to revoke the lease.")
        await get_client().delete_dhcp_lease(ip)
        return {"revoked": ip}

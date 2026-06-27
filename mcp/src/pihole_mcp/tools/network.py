"""Network device + ARP tools."""

from __future__ import annotations

from fastmcp import FastMCP

from pihole_mcp.server import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def list_network_devices() -> dict:
        """Every device FTL has seen on the LAN (broader than DHCP — includes static IPs)."""
        return await get_client().network_devices()

    @mcp.tool
    async def get_network_gateway() -> dict:
        """Current default gateway + interface."""
        return await get_client().network_gateway()

    @mcp.tool
    async def remove_network_device(device_id: int, confirm: bool = False) -> dict:
        """Delete a single device record (forgets it). Requires confirm=True."""
        if not confirm:
            raise ValueError("Set confirm=True to remove the device record.")
        await get_client().delete_network_device(device_id)
        return {"deleted_id": device_id}

    @mcp.tool
    async def flush_arp_cache(confirm: bool = False) -> dict:
        """Clear Pi-hole's ARP/network table. Rate-limited. Requires confirm=True."""
        if not confirm:
            raise ValueError("Set confirm=True to flush the ARP cache.")
        return await get_client().action_flush_arp()

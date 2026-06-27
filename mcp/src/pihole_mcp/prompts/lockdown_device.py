"""Slash command /lockdown_device <client> <level>."""

from __future__ import annotations

from typing import Literal

from fastmcp import FastMCP

Level = Literal["minimal", "strict", "unfiltered"]


def register(mcp: FastMCP) -> None:
    @mcp.prompt
    def lockdown_device(client_identifier: str, restriction_level: Level = "strict") -> str:
        """Move a device to a restrictive (or unfiltered) group with auto-discovery."""
        return (
            f"Move device **{client_identifier}** to a `{restriction_level}` filtering posture. Steps:\n"
            "1. Identify the device: try `get_client_detail(client=<id>)`; if not configured, "
            "call `list_unconfigured_clients` and find it there.\n"
            f"2. Locate (or create) the right group. Naming convention: `{restriction_level.title()}-Devices`. "
            "Use `list_groups`, then `create_group` if missing.\n"
            f"3. Update the client's group memberships to include the `{restriction_level}` group "
            "(and remove from looser ones if applicable).\n"
            "4. Warn me about iOS/macOS Private Wi-Fi Address rotation: if this is an Apple device, "
            "the MAC may rotate periodically and break the rule. Recommend disabling Private Wi-Fi "
            "Address for the home network on that device, or registering by IP with a DHCP reservation.\n"
            "5. Confirm with me before making the change. Use `update_client(... confirm=True)` "
            "for any mutation."
        )

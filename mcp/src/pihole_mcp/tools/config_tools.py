"""Pi-hole TOML config get/set tools (with safety allowlist on writes)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from pihole_mcp.server import get_client
from pihole_mcp.util.validators import is_safe_config_path


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_config(path: str | None = None, detailed: bool = False) -> dict:
        """Read full config (path=None) or a single element by dotted path."""
        c = get_client()
        if path is None:
            return await c.get_config(detailed=detailed)
        return await c.get_config_element(path)

    @mcp.tool
    async def list_config_keys() -> dict:
        """Top-level config tree (use as a map for get_config(path=...))."""
        return await get_client().get_config(detailed=False)

    @mcp.tool
    async def set_config(path: str, value: Any, confirm: bool = False) -> dict:
        """Set a config value. Path is dotted (`dns.upstreams`). Confirm required.

        Refuses writes to webserver.api.*, database.*, dns.port, files.*, debug.*
        (paths that could lock out the user or destroy data).
        """
        if not confirm:
            raise ValueError("Set confirm=True to change Pi-hole config.")
        if not is_safe_config_path(path):
            raise ValueError(
                f"Refusing to write {path!r}: this path is on the blocked-config allowlist "
                "to prevent lockout / data loss."
            )
        partial = _path_to_tree(path, value)
        return await get_client().patch_config(partial)

    @mcp.tool
    async def reset_config_value(path: str, value: str, confirm: bool = False) -> dict:
        """Delete a single value from an array-typed config setting."""
        if not confirm:
            raise ValueError("Set confirm=True to reset that config value.")
        if not is_safe_config_path(path):
            raise ValueError(f"Refusing to reset {path!r}: blocked config path.")
        await get_client().delete_config_value(path, value)
        return {"deleted": {"path": path, "value": value}}


def _path_to_tree(path: str, value: Any) -> dict[str, Any]:
    parts = path.split(".")
    if not parts:
        raise ValueError("path must be non-empty")
    root: dict[str, Any] = {}
    cursor = root
    for part in parts[:-1]:
        nxt: dict[str, Any] = {}
        cursor[part] = nxt
        cursor = nxt
    cursor[parts[-1]] = value
    return root

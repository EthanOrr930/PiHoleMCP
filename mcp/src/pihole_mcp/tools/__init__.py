"""Tool category registry. `register_all(mcp)` wires every category onto FastMCP."""

from __future__ import annotations

from fastmcp import FastMCP

from . import (
    adlists,
    clients,
    config_tools,
    dhcp,
    dns,
    domains,
    groups,
    history,
    logs,
    messages,
    network,
    queries,
    stats,
    system,
    teleporter,
)

_MODULES = (
    dns,
    domains,
    adlists,
    groups,
    clients,
    queries,
    stats,
    history,
    network,
    dhcp,
    system,
    config_tools,
    logs,
    teleporter,
    messages,
)


def register_all(mcp: FastMCP) -> None:
    for mod in _MODULES:
        mod.register(mcp)

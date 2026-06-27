"""Resource registry. `register_all(mcp)` wires every resource onto FastMCP."""

from __future__ import annotations

from fastmcp import FastMCP

from . import help as help_mod
from . import overview, recent_changes, topology

_MODULES = (overview, recent_changes, topology, help_mod)


def register_all(mcp: FastMCP) -> None:
    for mod in _MODULES:
        mod.register(mcp)

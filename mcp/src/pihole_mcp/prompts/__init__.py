"""Prompt (slash command) registry."""

from __future__ import annotations

from fastmcp import FastMCP

from . import audit_blocklists, daily_summary, investigate_block, lockdown_device, unblock_temporarily

_MODULES = (
    investigate_block,
    daily_summary,
    audit_blocklists,
    unblock_temporarily,
    lockdown_device,
)


def register_all(mcp: FastMCP) -> None:
    for mod in _MODULES:
        mod.register(mcp)

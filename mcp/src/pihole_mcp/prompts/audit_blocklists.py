"""Slash command /audit_blocklists."""

from __future__ import annotations

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt
    def audit_blocklists() -> str:
        """Walk the user through their adlists, flag stale ones for removal."""
        return (
            "Audit my Pi-hole adlists for stale or low-value sources. Steps:\n"
            "1. `list_adlists()` — pull every configured adlist.\n"
            "2. For each, surface: enabled, type, last update timestamp if available, comment.\n"
            "3. Identify candidates for removal:\n"
            "   - Disabled adlists that haven't been re-enabled in a long time.\n"
            "   - Duplicates or stale community lists that have been merged into bigger lists.\n"
            "   - Adlists whose source domain is no longer reachable.\n"
            "4. Present a Markdown table: name | url | status | recommendation.\n"
            "5. For anything you want to remove, ask me to confirm before calling "
            "`remove_adlist` (`confirm=True`).\n"
        )

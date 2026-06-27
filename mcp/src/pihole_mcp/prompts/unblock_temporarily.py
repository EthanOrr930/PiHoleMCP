"""Slash command /unblock_temporarily — temporary allow with auto-revert."""

from __future__ import annotations

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt
    def unblock_temporarily(domain: str, duration_minutes: int = 60) -> str:
        """Temporarily allow a blocked domain, auto-revert after N minutes."""
        capped = max(1, min(int(duration_minutes), 240))
        return (
            f"Temporarily unblock **{domain}** for **{capped} minutes**, then revert.\n\n"
            "Steps:\n"
            f"1. `find_why_blocked(domain='{domain}')` to confirm what's blocking it.\n"
            "2. Pick the narrowest fix: either an exact `allow_domain` rule or a regex "
            "allowlist entry scoped to my Default group.\n"
            "3. Add the allow rule with comment like 'temp allow <domain> (revert at <utc time>)'.\n"
            "4. Wait until I confirm the page loads.\n"
            f"5. Set a {capped}-minute timer for me to remember; or use `start_temp_job` "
            "(pseudo — actually you should just remind me at the end of this conversation "
            "to call `remove_domain_rule` on the rule you added, with confirm=True).\n"
            "Do NOT run `pause_blocking` — that disables blocking globally; we want a "
            "targeted, reversible exception.\n"
        )

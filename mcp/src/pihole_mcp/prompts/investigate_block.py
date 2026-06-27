"""Slash command /investigate_block <domain>."""

from __future__ import annotations

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt
    def investigate_block(domain: str) -> str:
        """Walk through diagnosing why a domain is blocked and propose an allow path."""
        return (
            f"I want to figure out why **{domain}** is being blocked by Pi-hole and decide whether "
            "to allow it.\n\n"
            "Please:\n"
            f"1. Call `find_why_blocked(domain='{domain}')` and present the sources.\n"
            "2. If it's blocked, summarize which adlists / rules / groups are responsible.\n"
            "3. Propose ONE of these resolutions and confirm with me before executing:\n"
            f"   - **Targeted allow**: `allow_domain(domain='{domain}', kind='exact')` "
            "scoped to my Default group (least invasive).\n"
            "   - **Remove the rule**: if a single rule is responsible and I don't need it.\n"
            "   - **Remove the adlist**: only if an entire adlist is misbehaving.\n"
            "4. Don't make any changes without my explicit OK.\n"
        )

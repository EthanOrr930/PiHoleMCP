"""Slash command /daily_summary."""

from __future__ import annotations

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt
    def daily_summary() -> str:
        """Generate a today-so-far Pi-hole report."""
        return (
            "Build me a 'Pi-hole today' summary. Steps:\n"
            "1. `get_stats_summary(source='live')` for headline numbers.\n"
            "2. `get_top_domains(source='live', blocked=True, limit=10)` for top blocked.\n"
            "3. `get_top_clients(source='live', limit=10)` for the loudest devices.\n"
            "4. `get_messages()` — surface anything in the diagnostic messages list.\n"
            "5. `get_gravity_status` if you find a recent job_id; otherwise skip.\n"
            "Format as concise Markdown: headline → top blocked → top clients → anomalies → "
            "warnings. Highlight anything that looks unusual (sudden spike, new top blocker, "
            "FTL warning, etc.)."
        )

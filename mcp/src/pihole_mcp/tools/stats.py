"""Live and database-backed stats tools."""

from __future__ import annotations

from typing import Literal

from fastmcp import FastMCP

from pihole_mcp.server import get_client

Source = Literal["live", "database"]


def _require_window(source: Source, from_ts: int | None, until_ts: int | None) -> None:
    if source == "database" and (from_ts is None or until_ts is None):
        raise ValueError("from_ts and until_ts (unix seconds) are required when source='database'.")


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_stats_summary(
        source: Source = "live",
        from_ts: int | None = None,
        until_ts: int | None = None,
    ) -> dict:
        """Pi-hole summary: total queries, blocked, %, gravity size, active clients, etc."""
        _require_window(source, from_ts, until_ts)
        c = get_client()
        return await (c.stats_db_summary(from_ts, until_ts) if source == "database" else c.stats_summary())

    @mcp.tool
    async def get_top_domains(
        source: Source = "live",
        blocked: bool = False,
        limit: int = 25,
        from_ts: int | None = None,
        until_ts: int | None = None,
    ) -> dict:
        """Top domains, either permitted (default) or blocked."""
        _require_window(source, from_ts, until_ts)
        c = get_client()
        return await (
            c.stats_db_top_domains(from_ts, until_ts, blocked=blocked, count=limit)
            if source == "database"
            else c.stats_top_domains(blocked=blocked, count=limit)
        )

    @mcp.tool
    async def get_top_clients(
        source: Source = "live",
        blocked: bool = False,
        limit: int = 25,
        from_ts: int | None = None,
        until_ts: int | None = None,
    ) -> dict:
        """Top clients by query volume (or blocked-query volume)."""
        _require_window(source, from_ts, until_ts)
        c = get_client()
        return await (
            c.stats_db_top_clients(from_ts, until_ts, blocked=blocked, count=limit)
            if source == "database"
            else c.stats_top_clients(blocked=blocked, count=limit)
        )

    @mcp.tool
    async def get_upstreams(
        source: Source = "live",
        from_ts: int | None = None,
        until_ts: int | None = None,
    ) -> dict:
        """Upstream-resolver breakdown."""
        _require_window(source, from_ts, until_ts)
        c = get_client()
        return await (c.stats_db_upstreams(from_ts, until_ts) if source == "database" else c.stats_upstreams())

    @mcp.tool
    async def get_query_types(
        source: Source = "live",
        from_ts: int | None = None,
        until_ts: int | None = None,
    ) -> dict:
        """Breakdown by DNS query type (A, AAAA, HTTPS, ...)."""
        _require_window(source, from_ts, until_ts)
        c = get_client()
        return await (c.stats_db_query_types(from_ts, until_ts) if source == "database" else c.stats_query_types())

    @mcp.tool
    async def get_db_content_summary(from_ts: int, until_ts: int) -> dict:
        """Database-backed metadata summary (storage, row counts) for the window."""
        return await get_client().stats_db_content(from_ts, until_ts)

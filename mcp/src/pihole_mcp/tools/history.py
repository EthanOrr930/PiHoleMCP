"""Activity time-series tools."""

from __future__ import annotations

from typing import Literal

from fastmcp import FastMCP

from pihole_mcp.server import get_client

Source = Literal["live", "database"]


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_activity_graph(
        source: Source = "live",
        from_ts: int | None = None,
        until_ts: int | None = None,
    ) -> dict:
        """24h rolling (live) or windowed (database) total/cached/blocked/forwarded time series."""
        c = get_client()
        if source == "database":
            if from_ts is None or until_ts is None:
                raise ValueError("from_ts and until_ts are required when source='database'.")
            return await c.history_database(from_ts, until_ts)
        return await c.history()

    @mcp.tool
    async def get_clients_activity(
        source: Source = "live",
        n: int = 25,
        from_ts: int | None = None,
        until_ts: int | None = None,
    ) -> dict:
        """Per-client activity time series (top N clients)."""
        c = get_client()
        if source == "database":
            if from_ts is None or until_ts is None:
                raise ValueError("from_ts and until_ts are required when source='database'.")
            return await c.history_database_clients(from_ts, until_ts, n=n)
        return await c.history_clients(n=n)

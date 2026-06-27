"""pihole://overview — live dashboard snapshot."""

from __future__ import annotations

import asyncio
import time

from fastmcp import FastMCP

from pihole_mcp.server import get_client
from pihole_mcp.util.cache import TTLCache

_CACHE = TTLCache(default_ttl=30.0)


def register(mcp: FastMCP) -> None:
    @mcp.resource("pihole://overview")
    async def overview() -> dict:
        """Live dashboard: blocking status, today's stats, top blocked, top clients."""
        cached = _CACHE.get("overview")
        if cached is not None:
            return cached
        snapshot = await _build()
        _CACHE.set("overview", snapshot)
        return snapshot


async def _build() -> dict:
    c = get_client()
    blocking, summary, top_blocked, top_clients, version = await asyncio.gather(
        c.get_blocking_status(),
        c.stats_summary(),
        c.stats_top_domains(blocked=True, count=10),
        c.stats_top_clients(count=10),
        c.info_version(),
        return_exceptions=True,
    )
    return {
        "generated_at": int(time.time()),
        "blocking": _unwrap(blocking),
        "summary": _unwrap(summary),
        "top_blocked": _unwrap(top_blocked),
        "top_clients": _unwrap(top_clients),
        "version": _unwrap(version),
    }


def _unwrap(v: object) -> object:
    if isinstance(v, BaseException):
        return {"error": f"{type(v).__name__}: {v}"}
    return v

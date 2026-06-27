"""pihole://topology — single-document map of groups + clients + rule counts."""

from __future__ import annotations

import asyncio
import time

from fastmcp import FastMCP

from pihole_mcp.server import get_client
from pihole_mcp.util.cache import TTLCache

_CACHE = TTLCache(default_ttl=60.0)


def register(mcp: FastMCP) -> None:
    @mcp.resource("pihole://topology")
    async def topology() -> dict:
        """Groups + clients + per-category rule counts in one snapshot."""
        cached = _CACHE.get("topo")
        if cached is not None:
            return cached
        snap = await _build()
        _CACHE.set("topo", snap)
        return snap


async def _build() -> dict:
    c = get_client()
    groups, clients, adlists, rules = await asyncio.gather(
        c.list_groups(),
        c.list_clients(),
        c.list_adlists(),
        c.list_domains(),
        return_exceptions=True,
    )
    return {
        "generated_at": int(time.time()),
        "groups": _unwrap(groups),
        "clients": _unwrap(clients),
        "adlists": _unwrap(adlists),
        "domain_rules": _unwrap(rules),
    }


def _unwrap(v: object) -> object:
    if isinstance(v, BaseException):
        return {"error": f"{type(v).__name__}: {v}"}
    return v

"""pihole://recent_changes — last 100 audit log entries."""

from __future__ import annotations

import json
from collections import deque

from fastmcp import FastMCP

from pihole_mcp.config import get_settings
from pihole_mcp.util.cache import TTLCache

_CACHE = TTLCache(default_ttl=10.0)
_MAX_ENTRIES = 100


def register(mcp: FastMCP) -> None:
    @mcp.resource("pihole://recent_changes")
    async def recent_changes() -> dict:
        """Last 100 tool-call audit entries, newest first."""
        cached = _CACHE.get("recent")
        if cached is not None:
            return cached
        entries = _tail_audit_log()
        out = {"count": len(entries), "entries": entries}
        _CACHE.set("recent", out)
        return out


def _tail_audit_log() -> list[dict]:
    path = get_settings().audit_log_path
    buf: deque[str] = deque(maxlen=_MAX_ENTRIES)
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                buf.append(line)
    except FileNotFoundError:
        return []
    out: list[dict] = []
    for raw in buf:
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    out.reverse()
    return out

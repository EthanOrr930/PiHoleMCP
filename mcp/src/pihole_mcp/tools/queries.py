"""Query log access tools."""

from __future__ import annotations

from fastmcp import FastMCP

from pihole_mcp.server import get_client

_HARD_QUERY_LIMIT = 1000
_HARD_RECENT_LIMIT = 100


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def tail_queries(
        since_cursor: int | None = None,
        limit: int = 100,
        domain: str | None = None,
        client_ip: str | None = None,
        client_name: str | None = None,
        upstream: str | None = None,
        type: str | None = None,
        status: str | None = None,
        from_ts: int | None = None,
        until_ts: int | None = None,
    ) -> dict:
        """Tail the Pi-hole DNS query log. Server caps `limit` at 1000."""
        capped = max(1, min(limit, _HARD_QUERY_LIMIT))
        return await get_client().get_queries(
            cursor=since_cursor,
            length=capped,
            domain=domain,
            client_ip=client_ip,
            client_name=client_name,
            upstream=upstream,
            type=type,
            status=status,
            **({"from": from_ts} if from_ts is not None else {}),
            **({"until": until_ts} if until_ts is not None else {}),
        )

    @mcp.tool
    async def get_query_filter_suggestions() -> dict:
        """Valid values for tail_queries filters (statuses, upstreams, types)."""
        return await get_client().get_query_suggestions()

    @mcp.tool
    async def get_recent_blocked(limit: int = 25) -> dict:
        """The most recent blocked queries (capped at 100)."""
        capped = max(1, min(limit, _HARD_RECENT_LIMIT))
        return await get_client().stats_recent_blocked(count=capped)

    @mcp.tool
    async def search_domain_in_lists(domain: str, n: int = 20, partial: bool = True) -> dict:
        """Search every adlist + domain rule for matches to `domain`."""
        return await get_client().search(domain, n=n, partial=partial)

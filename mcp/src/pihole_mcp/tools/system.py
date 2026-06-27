"""System info + destructive actions (gravity, restart, flush)."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from pihole_mcp.server import get_client, get_jobs


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_system_info() -> dict:
        """Composite Pi-hole system info: version, host, system, FTL stats."""
        c = get_client()
        version, system, host, ftl = await asyncio.gather(
            c.info_version(), c.info_system(), c.info_host(), c.info_ftl(),
            return_exceptions=True,
        )
        return {
            "version": _unwrap(version),
            "system": _unwrap(system),
            "host": _unwrap(host),
            "ftl": _unwrap(ftl),
        }

    @mcp.tool
    async def get_version_info() -> dict:
        """Pi-hole core/web/FTL versions."""
        return await get_client().info_version()

    @mcp.tool
    async def get_ftl_info() -> dict:
        """FTL daemon runtime info."""
        return await get_client().info_ftl()

    @mcp.tool
    async def get_host_info() -> dict:
        """Hostname, kernel, OS."""
        return await get_client().info_host()

    @mcp.tool
    async def get_metrics() -> dict:
        """Prometheus-style metrics from FTL."""
        return await get_client().info_metrics()

    @mcp.tool
    async def get_sensors_info() -> dict:
        """CPU temperature + fan sensors (where supported)."""
        return await get_client().info_sensors()

    @mcp.tool
    async def get_database_info() -> dict:
        """Gravity + query database file stats."""
        return await get_client().info_database()

    @mcp.tool
    async def run_gravity_update(confirm: bool = False) -> dict:
        """Run `pihole -g` to rebuild blocklists. Async job. Returns job_id."""
        if not confirm:
            raise ValueError("Set confirm=True to start a gravity update.")
        client = get_client()
        jobs = get_jobs()

        async def _gravity(progress: list[str]) -> dict:
            collected: list[str] = []
            async for line in client.action_gravity_stream():
                collected.append(line)
                progress.append(line)
                if len(progress) > 500:
                    del progress[: len(progress) - 500]
            return {"lines": len(collected)}

        job_id = jobs.start_job(_gravity)
        return {"job_id": job_id, "status": "started", "poll_with": "get_gravity_status"}

    @mcp.tool
    async def get_gravity_status(job_id: str) -> dict:
        """Poll status + recent progress lines for a gravity job."""
        status = get_jobs().get_status(job_id)
        if status is None:
            raise ValueError(f"Unknown job_id {job_id!r}.")
        return status

    @mcp.tool
    async def restart_dns(confirm: bool = False) -> dict:
        """Restart pihole-FTL. DNS goes down for ~3s. Rate-limited."""
        if not confirm:
            raise ValueError("Set confirm=True to restart Pi-hole DNS.")
        return await get_client().action_restart_dns()

    @mcp.tool
    async def flush_dns_logs(confirm: bool = False) -> dict:
        """Clear the live DNS query log. Rate-limited 1/hour."""
        if not confirm:
            raise ValueError("Set confirm=True to flush DNS logs.")
        return await get_client().action_flush_logs()


def _unwrap(v: object) -> object:
    if isinstance(v, BaseException):
        return {"error": f"{type(v).__name__}: {v}"}
    return v

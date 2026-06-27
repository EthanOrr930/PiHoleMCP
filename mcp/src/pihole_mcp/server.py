"""FastMCP server instance + lifecycle wiring."""

from __future__ import annotations

import asyncio
import signal
from typing import Any

import uvicorn
from fastmcp import FastMCP

from .config import Settings, get_settings
from .middleware.audit import AuditLogger, setup_logging
from .middleware.auth import BearerAuthMiddleware
from .middleware.origin import OriginCheckMiddleware
from .middleware.rate_limit import RateLimiter
from .pihole.client import PiHoleClient
from .util.jobs import JobTracker

mcp: FastMCP = FastMCP("pihole-mcp")

_client: PiHoleClient | None = None
_jobs: JobTracker | None = None
_audit: AuditLogger | None = None
_rate_limiter: RateLimiter | None = None


def get_client() -> PiHoleClient:
    if _client is None:
        raise RuntimeError("PiHoleClient not initialized; server.run() must be called first.")
    return _client


def get_jobs() -> JobTracker:
    if _jobs is None:
        raise RuntimeError("JobTracker not initialized.")
    return _jobs


def get_audit() -> AuditLogger:
    if _audit is None:
        raise RuntimeError("AuditLogger not initialized.")
    return _audit


def get_rate_limiter() -> RateLimiter:
    if _rate_limiter is None:
        raise RuntimeError("RateLimiter not initialized.")
    return _rate_limiter


def init_runtime(settings: Settings) -> None:
    """Build singletons + register tools/resources/prompts. Idempotent."""
    global _client, _jobs, _audit, _rate_limiter
    setup_logging(settings.log_level, settings.audit_log_path)
    _audit = AuditLogger(settings.audit_log_path)
    _rate_limiter = RateLimiter()
    _jobs = JobTracker()
    _client = PiHoleClient(settings.pihole_url, settings.pihole_app_password)
    from . import prompts, resources, tools  # late import — modules depend on get_client
    tools.register_all(mcp)
    resources.register_all(mcp)
    prompts.register_all(mcp)


def run(settings: Settings | None = None) -> None:
    s = settings or get_settings()
    init_runtime(s)
    app = mcp.http_app(path=s.mcp_path)
    app = BearerAuthMiddleware(app, expected_token=_load_bearer(s))
    app = OriginCheckMiddleware(app, allowed_origins=s.allowed_origins_list)

    config = uvicorn.Config(
        app,
        host=s.mcp_host,
        port=s.mcp_port,
        log_level=s.log_level.lower(),
        loop="asyncio",
        lifespan="on",
        workers=1,
    )
    server = uvicorn.Server(config)
    _install_shutdown_handlers(server)
    server.run()


def _load_bearer(s: Settings) -> str:
    token = (s.mcp_bearer_token or "").strip()
    if token:
        return token
    try:
        with open("/etc/pihole-mcp/token", "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _install_shutdown_handlers(server: uvicorn.Server) -> None:
    loop = asyncio.get_event_loop() if asyncio.get_event_loop_policy().get_event_loop().is_running() else None

    async def _shutdown() -> None:
        if _client is not None:
            await _client.aclose()

    def _handler(_sig: int, _frame: Any) -> None:
        server.should_exit = True
        try:
            asyncio.get_event_loop().create_task(_shutdown())
        except RuntimeError:
            pass

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _handler)
        except (ValueError, OSError):
            pass

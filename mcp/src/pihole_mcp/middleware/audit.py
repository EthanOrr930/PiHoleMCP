"""Structured audit logging for tool calls + setup helpers."""

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Any

import structlog

_REDACT_KEYS: frozenset[str] = frozenset({"password", "token", "secret", "app_password", "bearer", "sid", "csrf"})


def setup_logging(level: str, audit_log_path: str) -> structlog.stdlib.BoundLogger:
    """Wire up stdlib logging + structlog JSON for audit + general logs."""
    Path(audit_log_path).parent.mkdir(parents=True, exist_ok=True)

    audit_handler = logging.handlers.WatchedFileHandler(audit_log_path)
    audit_handler.setFormatter(logging.Formatter("%(message)s"))
    audit_logger = logging.getLogger("pihole_mcp.audit")
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False

    logging.basicConfig(level=level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s")

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger("pihole_mcp")


class AuditLogger:
    """Writes one JSON line per tool call to AUDIT_LOG_PATH."""

    def __init__(self, audit_log_path: str) -> None:
        self._path = audit_log_path
        self._logger = structlog.get_logger("pihole_mcp.audit").bind(component="audit")

    def log_tool_call(
        self,
        tool_name: str,
        params: dict[str, Any],
        outcome: str,
        duration_ms: float,
        error: str | None = None,
    ) -> None:
        self._logger.info(
            "tool_call",
            tool=tool_name,
            params=_redact(params),
            outcome=outcome,
            duration_ms=round(duration_ms, 2),
            error=error,
            pid=os.getpid(),
        )


def _redact(d: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in (d or {}).items():
        if isinstance(k, str) and k.lower() in _REDACT_KEYS:
            out[k] = "***"
        elif isinstance(v, dict):
            out[k] = _redact(v)
        else:
            out[k] = v
    return out

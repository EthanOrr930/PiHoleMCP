"""Middleware: auth + origin + rate limit + audit."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from pihole_mcp.middleware.audit import AuditLogger, setup_logging, _redact
from pihole_mcp.middleware.auth import BearerAuthMiddleware
from pihole_mcp.middleware.origin import OriginCheckMiddleware
from pihole_mcp.middleware.rate_limit import RateLimiter, RateLimited


class _DummyApp:
    def __init__(self) -> None:
        self.called = False

    async def __call__(self, scope, receive, send) -> None:
        self.called = True
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok", "more_body": False})


def _scope(headers=(), path="/mcp"):
    return {"type": "http", "path": path, "headers": list(headers)}


def _recorder():
    sent = []

    async def send(msg):
        sent.append(msg)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return sent, receive, send


@pytest.mark.asyncio
async def test_auth_rejects_missing_header():
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token="secret")
    sent, recv, send = _recorder()
    await mw(_scope(), recv, send)
    assert sent[0]["status"] == 401
    assert inner.called is False


@pytest.mark.asyncio
async def test_auth_rejects_wrong_token():
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token="secret")
    sent, recv, send = _recorder()
    await mw(_scope(headers=[(b"authorization", b"Bearer nope")]), recv, send)
    assert sent[0]["status"] == 401


@pytest.mark.asyncio
async def test_auth_allows_correct_token():
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token="secret")
    sent, recv, send = _recorder()
    await mw(_scope(headers=[(b"authorization", b"Bearer secret")]), recv, send)
    assert inner.called is True
    assert sent[0]["status"] == 200


@pytest.mark.asyncio
async def test_origin_allows_no_header():
    inner = _DummyApp()
    mw = OriginCheckMiddleware(inner, allowed_origins=["https://claude.ai"])
    sent, recv, send = _recorder()
    await mw(_scope(), recv, send)
    assert inner.called is True


@pytest.mark.asyncio
async def test_origin_rejects_disallowed():
    inner = _DummyApp()
    mw = OriginCheckMiddleware(inner, allowed_origins=["https://claude.ai"])
    sent, recv, send = _recorder()
    await mw(_scope(headers=[(b"origin", b"https://evil.example")]), recv, send)
    assert sent[0]["status"] == 403
    assert inner.called is False


@pytest.mark.asyncio
async def test_origin_allow_wildcard():
    inner = _DummyApp()
    mw = OriginCheckMiddleware(inner, allowed_origins=["*"])
    sent, recv, send = _recorder()
    await mw(_scope(headers=[(b"origin", b"https://anywhere.example")]), recv, send)
    assert inner.called is True


def test_rate_limit_default_allows_60_per_min():
    rl = RateLimiter()
    now = 1000.0
    for _ in range(60):
        rl.check("any_tool", now=now)
    with pytest.raises(RateLimited):
        rl.check("any_tool", now=now)


def test_rate_limit_sensitive_tool_throttled():
    rl = RateLimiter()
    now = 5000.0
    rl.check("flush_dns_logs", now=now)
    with pytest.raises(RateLimited):
        rl.check("flush_dns_logs", now=now + 1.0)


def test_redact_strips_sensitive_keys():
    redacted = _redact({"password": "p", "ok": 1, "nested": {"token": "t", "y": 2}})
    assert redacted == {"password": "***", "ok": 1, "nested": {"token": "***", "y": 2}}


def test_audit_logger_writes_json(tmp_path: Path):
    log_path = tmp_path / "audit.log"
    setup_logging("INFO", str(log_path))
    auditor = AuditLogger(str(log_path))
    auditor.log_tool_call("dummy_tool", {"x": 1, "password": "p"}, outcome="ok", duration_ms=1.5)
    time.sleep(0.05)
    content = log_path.read_text().strip().splitlines()
    assert content, "audit log should not be empty"
    parsed = json.loads(content[-1])
    assert parsed["tool"] == "dummy_tool"
    assert parsed["params"]["password"] == "***"
    assert parsed["outcome"] == "ok"

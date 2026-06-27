"""Bearer-token authentication ASGI middleware."""

from __future__ import annotations

import json
from typing import Awaitable, Callable

_SKIP_PATHS: frozenset[str] = frozenset({"/healthz", "/.well-known/oauth-protected-resource"})


class BearerAuthMiddleware:
    """Reject any request without `Authorization: Bearer <token>` matching expected.

    Wraps an ASGI app. /healthz bypasses for liveness probes.
    """

    def __init__(self, app, expected_token: str) -> None:
        self._app = app
        self._expected = expected_token

    async def __call__(self, scope, receive: Callable[[], Awaitable[dict]], send: Callable[[dict], Awaitable[None]]) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        if scope["path"] in _SKIP_PATHS:
            await self._app(scope, receive, send)
            return
        if not self._expected:
            await _unauthorized(send, "server has no bearer token configured")
            return
        token = _extract_bearer(scope.get("headers") or [])
        if token != self._expected:
            await _unauthorized(send, "missing or invalid bearer token")
            return
        await self._app(scope, receive, send)


def _extract_bearer(headers: list[tuple[bytes, bytes]]) -> str | None:
    for name, value in headers:
        if name.lower() == b"authorization":
            raw = value.decode("latin-1", "ignore").strip()
            if raw.lower().startswith("bearer "):
                return raw[7:].strip()
            return None
    return None


async def _unauthorized(send: Callable[[dict], Awaitable[None]], message: str) -> None:
    body = json.dumps({"error": "unauthorized", "message": message}).encode()
    await send({
        "type": "http.response.start",
        "status": 401,
        "headers": [
            (b"content-type", b"application/json"),
            (b"www-authenticate", b'Bearer realm="pihole-mcp"'),
            (b"content-length", str(len(body)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": body, "more_body": False})

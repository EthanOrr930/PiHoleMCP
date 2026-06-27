"""Origin-header allowlist ASGI middleware (DNS-rebinding defense)."""

from __future__ import annotations

import json
from typing import Awaitable, Callable


class OriginCheckMiddleware:
    """Reject requests whose Origin header is not on the allowlist.

    Requests without an Origin header (curl, server-to-server) are allowed
    through — the MCP spec only mandates this for browser-originated XHR.
    """

    def __init__(self, app, allowed_origins: list[str]) -> None:
        self._app = app
        self._allow_all = "*" in allowed_origins
        self._allowed = frozenset(o.lower() for o in allowed_origins)

    async def __call__(self, scope, receive: Callable[[], Awaitable[dict]], send: Callable[[dict], Awaitable[None]]) -> None:
        if scope["type"] != "http" or self._allow_all:
            await self._app(scope, receive, send)
            return
        origin = _header(scope.get("headers") or [], b"origin")
        if origin is None:
            await self._app(scope, receive, send)
            return
        if origin.lower() not in self._allowed:
            await _forbidden(send, f"origin {origin!r} not allowed")
            return
        await self._app(scope, receive, send)


def _header(headers: list[tuple[bytes, bytes]], name: bytes) -> str | None:
    for n, v in headers:
        if n.lower() == name:
            return v.decode("latin-1", "ignore")
    return None


async def _forbidden(send: Callable[[dict], Awaitable[None]], message: str) -> None:
    body = json.dumps({"error": "forbidden", "message": message}).encode()
    await send({
        "type": "http.response.start",
        "status": 403,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": body, "more_body": False})

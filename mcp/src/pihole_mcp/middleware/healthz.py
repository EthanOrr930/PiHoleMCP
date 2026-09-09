"""Liveness/readiness health endpoint for Kubernetes httpGet probes.

Sits as the outermost ASGI middleware so /healthz is answered with 200 OK
before BearerAuth or OriginCheck run — kubelet probes carry no Authorization
header and no Origin header, so they must not be subject to either check.
"""
from __future__ import annotations

from typing import Awaitable, Callable

_HEALTHZ_PATH = "/healthz"
_OK_BODY = b'{"status":"ok"}'


class HealthzMiddleware:
    """Answer GET /healthz with 200 OK; pass everything else through."""

    def __init__(self, app) -> None:
        self._app = app

    async def __call__(
        self,
        scope,
        receive: Callable[[], Awaitable[dict]],
        send: Callable[[dict], Awaitable[None]],
    ) -> None:
        if scope.get("type") == "http" and scope.get("path") == _HEALTHZ_PATH:
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(_OK_BODY)).encode()),
                    ],
                }
            )
            await send(
                {"type": "http.response.body", "body": _OK_BODY, "more_body": False}
            )
            return
        await self._app(scope, receive, send)
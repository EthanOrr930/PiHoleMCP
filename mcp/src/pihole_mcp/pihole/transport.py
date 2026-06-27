"""HTTP transport layer for the Pi-hole client.

Handles SID injection, 401 retry, status-code -> exception mapping, and a TTL
cache for read-only descriptor calls. Knows nothing about Pi-hole endpoints.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from ..util.cache import TTLCache
from .errors import (
    AuthError,
    DestructiveActionsDisabled,
    InvalidRegex,
    NotFound,
    PiHoleError,
    PiHoleRateLimited,
    PiHoleSeatExhausted,
    PiHoleServerError,
    PiHoleTimeout,
)
from .session import SessionManager

_DEFAULT_EXPECT: tuple[int, ...] = (200, 201, 202, 204)


class RequestRunner:
    """Single-purpose: send an authenticated HTTP request, map errors, cache GETs."""

    def __init__(self, http: httpx.AsyncClient, session: SessionManager, cache: TTLCache) -> None:
        self._http = http
        self._session = session
        self._cache = cache

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
        retry: bool = True,
        expect_status: tuple[int, ...] = _DEFAULT_EXPECT,
    ) -> Any:
        sid = await self._session.get_sid()
        try:
            resp = await self._http.request(
                method, path, json=json_body, params=params, headers={"X-FTL-SID": sid}
            )
        except httpx.TimeoutException as e:
            raise PiHoleTimeout(f"Timeout calling {method} {path}") from e
        except httpx.HTTPError as e:
            raise PiHoleServerError(f"HTTP error on {method} {path}: {e}") from e

        if resp.status_code == 401 and retry:
            await self._session.invalidate()
            return await self.request(
                method, path, json_body=json_body, params=params, retry=False, expect_status=expect_status
            )

        _raise_for_status(resp, method, path, expect_status)
        if resp.status_code == 204 or not resp.content:
            return None
        if "application/json" in resp.headers.get("content-type", ""):
            return resp.json()
        return resp.content

    async def cached_get(self, path: str, *, params: dict[str, Any] | None = None, ttl: float = 60.0) -> Any:
        key = f"GET {path}?{json.dumps(params or {}, sort_keys=True)}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        result = await self.request("GET", path, params=params)
        self._cache.set(key, result, ttl=ttl)
        return result

    def invalidate(self, *prefixes: str) -> None:
        for p in prefixes:
            self._cache.invalidate_prefix(f"GET {p}")


def _raise_for_status(resp: httpx.Response, method: str, path: str, expect: tuple[int, ...]) -> None:
    if resp.status_code in expect:
        return
    body: Any
    try:
        body = resp.json()
    except Exception:
        body = resp.text
    err_key: str | None = None
    if isinstance(body, dict):
        err = body.get("error") or {}
        if isinstance(err, dict):
            err_key = err.get("key")
    sc = resp.status_code
    msg = f"Pi-hole {sc} on {method} {path}"
    if sc == 401:
        raise AuthError(msg, status=sc, payload=body)
    if sc == 403 and err_key == "forbidden":
        raise DestructiveActionsDisabled(msg, status=sc, payload=body)
    if sc == 404:
        raise NotFound(msg, status=sc, payload=body)
    if sc == 400 and err_key == "regex_error":
        raise InvalidRegex(msg, status=sc, payload=body)
    if sc == 429:
        if err_key == "no_free_seats":
            raise PiHoleSeatExhausted(msg, status=sc, payload=body)
        raise PiHoleRateLimited(msg, status=sc, payload=body)
    if sc >= 500:
        raise PiHoleServerError(msg, status=sc, payload=body)
    raise PiHoleError(msg, status=sc, payload=body)

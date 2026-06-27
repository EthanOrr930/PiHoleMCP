"""Pi-hole SID lifecycle — lazy auth, single-flight, expiry tracking."""

from __future__ import annotations

import asyncio
import time

import httpx

from .errors import (
    AuthError,
    PiHoleRateLimited,
    PiHoleSeatExhausted,
    PiHoleServerError,
    PiHoleTimeout,
)

_SAFETY_MARGIN_S = 30


class SessionManager:
    """Owns the Pi-hole session id (SID) for one PiHoleClient.

    All callers race through `get_sid()`; a single asyncio.Lock guarantees
    we never run two `/api/auth` requests concurrently.
    """

    def __init__(self, http: httpx.AsyncClient, app_password: str) -> None:
        self._http = http
        self._password = app_password
        self._lock = asyncio.Lock()
        self._sid: str | None = None
        self._expires_at: float = 0.0

    async def get_sid(self) -> str:
        if self._is_fresh():
            return self._sid  # type: ignore[return-value]
        async with self._lock:
            if self._is_fresh():
                return self._sid  # type: ignore[return-value]
            await self._authenticate()
            return self._sid  # type: ignore[return-value]

    async def invalidate(self) -> None:
        async with self._lock:
            self._sid = None
            self._expires_at = 0.0

    async def shutdown(self) -> None:
        sid = self._sid
        if not sid:
            return
        try:
            await self._http.request("DELETE", "/api/auth", headers={"X-FTL-SID": sid})
        except Exception:
            pass
        await self.invalidate()

    def _is_fresh(self) -> bool:
        return self._sid is not None and time.monotonic() < self._expires_at

    async def _authenticate(self) -> None:
        try:
            resp = await self._http.post("/api/auth", json={"password": self._password})
        except httpx.TimeoutException as e:
            raise PiHoleTimeout("Timed out contacting Pi-hole /api/auth") from e
        except httpx.HTTPError as e:
            raise PiHoleServerError(f"HTTP error during auth: {e}") from e

        if resp.status_code == 429:
            self._raise_429(resp)
        if resp.status_code >= 500:
            raise PiHoleServerError(f"Pi-hole {resp.status_code} on /api/auth", status=resp.status_code)
        if resp.status_code in (401, 403):
            raise AuthError("Pi-hole rejected app password", status=resp.status_code)
        if resp.status_code != 200:
            raise AuthError(f"Unexpected auth status {resp.status_code}", status=resp.status_code)

        body = resp.json()
        sess = body.get("session") or {}
        if not sess.get("valid") or not sess.get("sid"):
            raise AuthError(sess.get("message") or "Pi-hole auth returned invalid session", payload=body)

        self._sid = sess["sid"]
        validity = int(sess.get("validity") or 300)
        self._expires_at = time.monotonic() + max(validity - _SAFETY_MARGIN_S, 1)

    @staticmethod
    def _raise_429(resp: httpx.Response) -> None:
        try:
            body = resp.json()
        except Exception:
            body = None
        if isinstance(body, dict):
            err = body.get("error") or {}
            if isinstance(err, dict) and err.get("key") == "no_free_seats":
                raise PiHoleSeatExhausted("Pi-hole has no free session seats", status=429, payload=body)
        raise PiHoleRateLimited("Pi-hole rate limited the request", status=429, payload=body)

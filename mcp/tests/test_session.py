"""SessionManager: SID lifecycle correctness."""

from __future__ import annotations

import asyncio

import httpx
import pytest
import pytest_asyncio
import respx

from pihole_mcp.pihole.errors import AuthError, PiHoleSeatExhausted
from pihole_mcp.pihole.session import SessionManager

PIHOLE = "http://test-pihole"
GOOD_AUTH = {
    "session": {"sid": "sid-abc", "csrf": "c", "valid": True, "validity": 300, "message": None},
    "took": 0.001,
}


@pytest_asyncio.fixture
async def http() -> httpx.AsyncClient:
    async with httpx.AsyncClient(base_url=PIHOLE) as c:
        yield c


@pytest.mark.asyncio
async def test_cold_auth_calls_endpoint(respx_mock, http):
    route = respx_mock.post(f"{PIHOLE}/api/auth").mock(return_value=httpx.Response(200, json=GOOD_AUTH))
    sm = SessionManager(http, "pwd")
    sid = await sm.get_sid()
    assert sid == "sid-abc"
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_sid_cached_no_second_call(respx_mock, http):
    route = respx_mock.post(f"{PIHOLE}/api/auth").mock(return_value=httpx.Response(200, json=GOOD_AUTH))
    sm = SessionManager(http, "pwd")
    await sm.get_sid()
    await sm.get_sid()
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_invalidate_triggers_reauth(respx_mock, http):
    route = respx_mock.post(f"{PIHOLE}/api/auth").mock(return_value=httpx.Response(200, json=GOOD_AUTH))
    sm = SessionManager(http, "pwd")
    await sm.get_sid()
    await sm.invalidate()
    await sm.get_sid()
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_concurrent_get_sid_singleflight(respx_mock, http):
    route = respx_mock.post(f"{PIHOLE}/api/auth").mock(return_value=httpx.Response(200, json=GOOD_AUTH))
    sm = SessionManager(http, "pwd")
    sids = await asyncio.gather(*[sm.get_sid() for _ in range(10)])
    assert set(sids) == {"sid-abc"}
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_401_raises_auth_error(respx_mock, http):
    respx_mock.post(f"{PIHOLE}/api/auth").mock(return_value=httpx.Response(401, json={"error": "nope"}))
    sm = SessionManager(http, "pwd")
    with pytest.raises(AuthError):
        await sm.get_sid()


@pytest.mark.asyncio
async def test_429_no_free_seats_raises_seat_exhausted(respx_mock, http):
    respx_mock.post(f"{PIHOLE}/api/auth").mock(
        return_value=httpx.Response(429, json={"error": {"key": "no_free_seats"}})
    )
    sm = SessionManager(http, "pwd")
    with pytest.raises(PiHoleSeatExhausted):
        await sm.get_sid()


@pytest.mark.asyncio
async def test_shutdown_sends_delete(respx_mock, http):
    respx_mock.post(f"{PIHOLE}/api/auth").mock(return_value=httpx.Response(200, json=GOOD_AUTH))
    delete_route = respx_mock.delete(f"{PIHOLE}/api/auth").mock(return_value=httpx.Response(204))
    sm = SessionManager(http, "pwd")
    await sm.get_sid()
    await sm.shutdown()
    assert delete_route.call_count == 1

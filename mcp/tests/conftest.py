"""Shared pytest fixtures: mock Pi-hole via respx + a wired-up PiHoleClient."""

from __future__ import annotations

import httpx
import pytest
import pytest_asyncio
import respx

from pihole_mcp.pihole.client import PiHoleClient


PIHOLE_BASE = "http://test-pihole"
APP_PWD = "test-app-password"
SID = "test-sid-123"
DEFAULT_AUTH = {
    "session": {
        "sid": SID,
        "csrf": "csrf-x",
        "valid": True,
        "validity": 300,
        "totp": False,
        "message": None,
    },
    "took": 0.001,
}


@pytest.fixture
def pihole_url() -> str:
    return PIHOLE_BASE


@pytest.fixture
def app_password() -> str:
    return APP_PWD


@pytest_asyncio.fixture
async def mock_pihole(respx_mock):
    respx_mock.post(f"{PIHOLE_BASE}/api/auth").mock(return_value=httpx.Response(200, json=DEFAULT_AUTH))
    respx_mock.delete(f"{PIHOLE_BASE}/api/auth").mock(return_value=httpx.Response(204))
    yield respx_mock


@pytest_asyncio.fixture
async def client(mock_pihole) -> PiHoleClient:
    c = PiHoleClient(PIHOLE_BASE, APP_PWD)
    try:
        yield c
    finally:
        await c.aclose()

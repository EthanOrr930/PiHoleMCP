"""PiHoleClient: endpoint method round-trips against respx mock."""

from __future__ import annotations

import httpx
import pytest

from pihole_mcp.pihole.errors import (
    AuthError,
    DestructiveActionsDisabled,
    NotFound,
    PiHoleServerError,
)


@pytest.mark.asyncio
async def test_get_blocking_status(client, mock_pihole):
    mock_pihole.get("http://test-pihole/api/dns/blocking").mock(
        return_value=httpx.Response(200, json={"blocking": "enabled", "timer": None, "took": 0.001})
    )
    out = await client.get_blocking_status()
    assert out["blocking"] == "enabled"


@pytest.mark.asyncio
async def test_set_blocking_sends_body(client, mock_pihole):
    route = mock_pihole.post("http://test-pihole/api/dns/blocking").mock(
        return_value=httpx.Response(200, json={"blocking": "disabled", "timer": 600, "took": 0.001})
    )
    out = await client.set_blocking(blocking=False, timer=600)
    assert out["timer"] == 600
    body = route.calls[0].request.read().decode()
    assert '"blocking": false' in body
    assert '"timer": 600' in body


@pytest.mark.asyncio
async def test_groups_crud_roundtrip(client, mock_pihole):
    mock_pihole.get("http://test-pihole/api/groups").mock(
        return_value=httpx.Response(200, json={"groups": [{"id": 0, "name": "Default", "enabled": True}], "took": 0.001})
    )
    mock_pihole.post("http://test-pihole/api/groups").mock(
        return_value=httpx.Response(201, json={"groups": [{"id": 1, "name": "kids", "enabled": True}], "took": 0.001})
    )
    mock_pihole.delete("http://test-pihole/api/groups/kids").mock(return_value=httpx.Response(204))

    lst = await client.list_groups()
    assert lst["groups"][0]["name"] == "Default"
    created = await client.create_group("kids")
    assert created["groups"][0]["name"] == "kids"
    await client.delete_group("kids")


@pytest.mark.asyncio
async def test_403_destructive(client, mock_pihole):
    mock_pihole.post("http://test-pihole/api/action/restartdns").mock(return_value=httpx.Response(403, json={"error": {"key": "destructive_disabled"}}))
    with pytest.raises(DestructiveActionsDisabled):
        await client.action_restart_dns()


@pytest.mark.asyncio
async def test_404_raises_not_found(client, mock_pihole):
    mock_pihole.get("http://test-pihole/api/groups/nope").mock(return_value=httpx.Response(404, json={"error": {"key": "not_found"}}))
    with pytest.raises(NotFound):
        await client.get_group("nope")


@pytest.mark.asyncio
async def test_500_raises_server_error(client, mock_pihole):
    mock_pihole.get("http://test-pihole/api/info/system").mock(return_value=httpx.Response(500, text="boom"))
    with pytest.raises(PiHoleServerError):
        await client.info_system()


@pytest.mark.asyncio
async def test_401_then_reauth_then_success(client, mock_pihole):
    calls = {"n": 0}

    def responder(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(401, json={"error": {"key": "unauthorized"}})
        return httpx.Response(200, json={"blocking": "enabled", "took": 0.001})

    mock_pihole.get("http://test-pihole/api/dns/blocking").mock(side_effect=responder)
    out = await client.get_blocking_status()
    assert out["blocking"] == "enabled"


@pytest.mark.asyncio
async def test_401_twice_raises_auth_error(client, mock_pihole):
    mock_pihole.get("http://test-pihole/api/dns/blocking").mock(return_value=httpx.Response(401, json={"error": {"key": "unauthorized"}}))
    with pytest.raises(AuthError):
        await client.get_blocking_status()

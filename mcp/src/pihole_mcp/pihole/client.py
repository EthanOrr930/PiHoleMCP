"""Async Pi-hole v6 REST client — one method per endpoint."""

from __future__ import annotations

from typing import Any, AsyncIterator, Literal
from urllib.parse import quote

import httpx

from ..util.cache import TTLCache
from .errors import AuthError, DestructiveActionsDisabled, PiHoleError
from .session import SessionManager
from .transport import RequestRunner

_DEFAULT_TIMEOUT = 30.0
_DESCRIPTOR_TTL = 60.0

DomainType = Literal["allow", "deny"]
DomainKind = Literal["exact", "regex"]


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _enc(s: str) -> str:
    return quote(s, safe="")


class PiHoleClient:
    """Facade over the Pi-hole v6 REST API. One method per endpoint."""

    def __init__(self, base_url: str, app_password: str) -> None:
        self._http = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=_DEFAULT_TIMEOUT)
        self._session = SessionManager(self._http, app_password)
        self._cache = TTLCache(default_ttl=_DESCRIPTOR_TTL)
        self._rr = RequestRunner(self._http, self._session, self._cache)

    async def aclose(self) -> None:
        try:
            await self._session.shutdown()
        finally:
            await self._http.aclose()

    # --- DNS blocking ----------------------------------------------------------

    async def get_blocking_status(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/dns/blocking")

    async def set_blocking(self, blocking: bool, timer: int | None = None) -> dict[str, Any]:
        return await self._rr.request("POST", "/api/dns/blocking", json_body={"blocking": blocking, "timer": timer})

    # --- domain rules ----------------------------------------------------------

    async def list_domains(self, **filters: Any) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/domains", params=_drop_none(filters))

    async def get_domain(self, type_: DomainType, kind: DomainKind, domain: str) -> dict[str, Any]:
        return await self._rr.request("GET", f"/api/domains/{type_}/{kind}/{_enc(domain)}")

    async def create_domain(self, type_: DomainType, kind: DomainKind, **body: Any) -> dict[str, Any]:
        self._rr.invalidate("/api/domains")
        return await self._rr.request("POST", f"/api/domains/{type_}/{kind}", json_body=_drop_none(body))

    async def update_domain(self, type_: DomainType, kind: DomainKind, domain: str, **fields: Any) -> dict[str, Any]:
        self._rr.invalidate("/api/domains")
        return await self._rr.request("PUT", f"/api/domains/{type_}/{kind}/{_enc(domain)}", json_body=_drop_none(fields))

    async def delete_domain(self, type_: DomainType, kind: DomainKind, domain: str) -> None:
        self._rr.invalidate("/api/domains")
        await self._rr.request("DELETE", f"/api/domains/{type_}/{kind}/{_enc(domain)}")

    async def batch_delete_domains(self, items: list[dict[str, str]]) -> None:
        self._rr.invalidate("/api/domains")
        await self._rr.request("POST", "/api/domains:batchDelete", json_body=items)

    # --- adlists ---------------------------------------------------------------

    async def list_adlists(self, **filters: Any) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/lists", params=_drop_none(filters))

    async def get_adlist(self, address: str) -> dict[str, Any]:
        return await self._rr.request("GET", f"/api/lists/{_enc(address)}")

    async def create_adlist(self, **body: Any) -> dict[str, Any]:
        self._rr.invalidate("/api/lists")
        return await self._rr.request("POST", "/api/lists", json_body=_drop_none(body))

    async def update_adlist(self, address: str, **fields: Any) -> dict[str, Any]:
        self._rr.invalidate("/api/lists")
        return await self._rr.request("PUT", f"/api/lists/{_enc(address)}", json_body=_drop_none(fields))

    async def delete_adlist(self, address: str, type_: str | None = None) -> None:
        self._rr.invalidate("/api/lists")
        await self._rr.request("DELETE", f"/api/lists/{_enc(address)}", params={"type": type_} if type_ else None)

    async def batch_delete_adlists(self, items: list[dict[str, str]]) -> None:
        self._rr.invalidate("/api/lists")
        await self._rr.request("POST", "/api/lists:batchDelete", json_body=items)

    # --- groups ----------------------------------------------------------------

    async def list_groups(self) -> dict[str, Any]:
        return await self._rr.cached_get("/api/groups")

    async def get_group(self, name: str) -> dict[str, Any]:
        return await self._rr.request("GET", f"/api/groups/{_enc(name)}")

    async def create_group(self, name: str, comment: str | None = None, enabled: bool = True) -> dict[str, Any]:
        self._rr.invalidate("/api/groups")
        return await self._rr.request("POST", "/api/groups", json_body={"name": name, "comment": comment, "enabled": enabled})

    async def update_group(self, name: str, **fields: Any) -> dict[str, Any]:
        self._rr.invalidate("/api/groups")
        return await self._rr.request("PUT", f"/api/groups/{_enc(name)}", json_body=_drop_none(fields))

    async def delete_group(self, name: str) -> None:
        self._rr.invalidate("/api/groups")
        await self._rr.request("DELETE", f"/api/groups/{_enc(name)}")

    async def batch_delete_groups(self, names: list[str]) -> None:
        self._rr.invalidate("/api/groups")
        await self._rr.request("POST", "/api/groups:batchDelete", json_body=[{"item": n} for n in names])

    # --- clients ---------------------------------------------------------------

    async def list_clients(self) -> dict[str, Any]:
        return await self._rr.cached_get("/api/clients")

    async def get_client_suggestions(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/clients/_suggestions")

    async def get_client(self, client: str) -> dict[str, Any]:
        return await self._rr.request("GET", f"/api/clients/{_enc(client)}")

    async def add_client(self, client: str, comment: str | None = None, groups: list[int] | None = None) -> dict[str, Any]:
        self._rr.invalidate("/api/clients")
        return await self._rr.request("POST", "/api/clients", json_body={"client": client, "comment": comment, "groups": groups})

    async def update_client(self, client: str, **fields: Any) -> dict[str, Any]:
        self._rr.invalidate("/api/clients")
        return await self._rr.request("PUT", f"/api/clients/{_enc(client)}", json_body=_drop_none(fields))

    async def delete_client(self, client: str) -> None:
        self._rr.invalidate("/api/clients")
        await self._rr.request("DELETE", f"/api/clients/{_enc(client)}")

    async def batch_delete_clients(self, clients: list[str]) -> None:
        self._rr.invalidate("/api/clients")
        await self._rr.request("POST", "/api/clients:batchDelete", json_body=[{"item": c} for c in clients])

    # --- query log -------------------------------------------------------------

    async def get_queries(self, **filters: Any) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/queries", params=_drop_none(filters))

    async def get_query_suggestions(self) -> dict[str, Any]:
        return await self._rr.cached_get("/api/queries/suggestions")

    # --- live stats ------------------------------------------------------------

    async def stats_summary(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/summary")

    async def stats_top_domains(self, blocked: bool | None = None, count: int | None = None) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/top_domains", params=_drop_none({"blocked": blocked, "count": count}))

    async def stats_top_clients(self, blocked: bool | None = None, count: int | None = None) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/top_clients", params=_drop_none({"blocked": blocked, "count": count}))

    async def stats_upstreams(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/upstreams")

    async def stats_query_types(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/query_types")

    async def stats_recent_blocked(self, count: int | None = None) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/recent_blocked", params=_drop_none({"count": count}))

    # --- database-backed stats -------------------------------------------------

    async def stats_db_summary(self, from_: int, until: int) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/database/summary", params={"from": from_, "until": until})

    async def stats_db_top_domains(self, from_: int, until: int, blocked: bool | None = None, count: int | None = None) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/database/top_domains", params=_drop_none({"from": from_, "until": until, "blocked": blocked, "count": count}))

    async def stats_db_top_clients(self, from_: int, until: int, blocked: bool | None = None, count: int | None = None) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/database/top_clients", params=_drop_none({"from": from_, "until": until, "blocked": blocked, "count": count}))

    async def stats_db_upstreams(self, from_: int, until: int) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/database/upstreams", params={"from": from_, "until": until})

    async def stats_db_query_types(self, from_: int, until: int) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/database/query_types", params={"from": from_, "until": until})

    async def stats_db_content(self, from_: int, until: int) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/stats/database/content", params={"from": from_, "until": until})

    # --- history ---------------------------------------------------------------

    async def history(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/history")

    async def history_clients(self, n: int | None = None) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/history/clients", params=_drop_none({"N": n}))

    async def history_database(self, from_: int, until: int) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/history/database", params={"from": from_, "until": until})

    async def history_database_clients(self, from_: int, until: int, n: int | None = None) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/history/database/clients", params=_drop_none({"from": from_, "until": until, "N": n}))

    # --- network + DHCP -------------------------------------------------------

    async def network_devices(self) -> dict[str, Any]:
        return await self._rr.cached_get("/api/network/devices")

    async def network_gateway(self) -> dict[str, Any]:
        return await self._rr.cached_get("/api/network/gateway")

    async def delete_network_device(self, device_id: int) -> None:
        self._rr.invalidate("/api/network")
        await self._rr.request("DELETE", f"/api/network/devices/{int(device_id)}")

    async def dhcp_leases(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/dhcp/leases")

    async def delete_dhcp_lease(self, ip: str) -> None:
        await self._rr.request("DELETE", f"/api/dhcp/leases/{_enc(ip)}")

    # --- config ----------------------------------------------------------------

    async def get_config(self, detailed: bool = False) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/config", params={"detailed": "true" if detailed else "false"})

    async def get_config_element(self, element_path: str) -> dict[str, Any]:
        return await self._rr.request("GET", f"/api/config/{element_path}")

    async def patch_config(self, partial: dict[str, Any]) -> dict[str, Any]:
        self._rr.invalidate("/api/config")
        return await self._rr.request("PATCH", "/api/config", json_body={"config": partial})

    async def put_config_value(self, element_path: str, value: str) -> dict[str, Any]:
        self._rr.invalidate("/api/config")
        return await self._rr.request("PUT", f"/api/config/{element_path}/{_enc(value)}")

    async def delete_config_value(self, element_path: str, value: str) -> None:
        self._rr.invalidate("/api/config")
        await self._rr.request("DELETE", f"/api/config/{element_path}/{_enc(value)}")

    # --- info ------------------------------------------------------------------

    async def info_version(self) -> dict[str, Any]:
        return await self._rr.cached_get("/api/info/version", ttl=300)

    async def info_system(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/info/system")

    async def info_host(self) -> dict[str, Any]:
        return await self._rr.cached_get("/api/info/host", ttl=300)

    async def info_ftl(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/info/ftl")

    async def info_sensors(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/info/sensors")

    async def info_login(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/info/login")

    async def info_metrics(self) -> Any:
        return await self._rr.request("GET", "/api/info/metrics")

    async def info_database(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/info/database")

    async def info_client(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/info/client")

    async def info_messages(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/info/messages")

    async def info_messages_count(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/info/messages/count")

    async def delete_info_message(self, message_id: int) -> None:
        await self._rr.request("DELETE", f"/api/info/messages/{int(message_id)}")

    # --- destructive actions ---------------------------------------------------

    async def action_restart_dns(self) -> dict[str, Any]:
        return await self._rr.request("POST", "/api/action/restartdns")

    async def action_flush_logs(self) -> dict[str, Any]:
        return await self._rr.request("POST", "/api/action/flush/logs")

    async def action_flush_arp(self) -> dict[str, Any]:
        return await self._rr.request("POST", "/api/action/flush/arp")

    async def action_gravity_stream(self) -> AsyncIterator[str]:
        """Yield raw text/event-stream lines from /api/action/gravity."""
        sid = await self._session.get_sid()
        headers = {"X-FTL-SID": sid, "Accept": "text/event-stream"}
        async with self._http.stream("POST", "/api/action/gravity", headers=headers) as resp:
            if resp.status_code == 401:
                await self._session.invalidate()
                raise AuthError("Pi-hole rejected SID during gravity stream", status=401)
            if resp.status_code == 403:
                raise DestructiveActionsDisabled("Destructive actions disabled", status=403)
            if resp.status_code >= 400:
                raise PiHoleError(f"Pi-hole {resp.status_code} on gravity action", status=resp.status_code)
            async for line in resp.aiter_lines():
                if line:
                    yield line

    # --- logs ------------------------------------------------------------------

    async def logs_dnsmasq(self, next_id: int | None = None) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/logs/dnsmasq", params=_drop_none({"nextID": next_id}))

    async def logs_ftl(self, next_id: int | None = None) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/logs/ftl", params=_drop_none({"nextID": next_id}))

    async def logs_webserver(self, next_id: int | None = None) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/logs/webserver", params=_drop_none({"nextID": next_id}))

    # --- teleporter + search --------------------------------------------------

    async def teleporter_export(self) -> bytes:
        result = await self._rr.request("GET", "/api/teleporter")
        return result if isinstance(result, bytes) else bytes(result)

    async def teleporter_import(self, zip_bytes: bytes) -> dict[str, Any]:
        sid = await self._session.get_sid()
        resp = await self._http.post(
            "/api/teleporter",
            headers={"X-FTL-SID": sid},
            files={"file": ("pihole.zip", zip_bytes, "application/zip")},
        )
        if resp.status_code not in (200, 201):
            raise PiHoleError(f"Pi-hole {resp.status_code} on teleporter import", status=resp.status_code)
        return resp.json()

    async def search(self, domain: str, n: int | None = None, partial: bool | None = None) -> dict[str, Any]:
        params: dict[str, Any] = _drop_none({
            "N": n,
            "partial": ("true" if partial else "false") if partial is not None else None,
        })
        return await self._rr.request("GET", f"/api/search/{_enc(domain)}", params=params or None)

    async def endpoints(self) -> dict[str, Any]:
        return await self._rr.cached_get("/api/endpoints", ttl=3600)

    async def auth_status(self) -> dict[str, Any]:
        return await self._rr.request("GET", "/api/auth")

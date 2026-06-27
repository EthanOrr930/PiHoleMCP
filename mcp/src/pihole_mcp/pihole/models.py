"""Loose Pydantic v2 models for common Pi-hole v6 response shapes.

Pi-hole frequently adds fields between minor versions; every model uses
`extra="allow"` so unknown keys round-trip through `.model_dump()`.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _Loose(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Session(_Loose):
    sid: str | None = None
    csrf: str | None = None
    valid: bool = False
    totp: bool = False
    validity: int = 0
    message: str | None = None


class BlockingStatus(_Loose):
    blocking: Literal["enabled", "disabled", "failed", "unknown"] = "unknown"
    timer: int | None = None


class DomainRule(_Loose):
    domain: str
    type: Literal["allow", "deny"]
    kind: Literal["exact", "regex"]
    enabled: bool = True
    comment: str | None = None
    groups: list[int] = Field(default_factory=list)
    id: int | None = None
    date_added: int | None = None
    date_modified: int | None = None


class Adlist(_Loose):
    address: str
    type: Literal["block", "allow"] = "block"
    enabled: bool = True
    comment: str | None = None
    groups: list[int] = Field(default_factory=list)
    id: int | None = None
    date_added: int | None = None
    date_modified: int | None = None
    date_updated: int | None = None
    number: int | None = None
    invalid_domains: int | None = None
    abp_entries: int | None = None
    status: int | None = None


class Group(_Loose):
    name: str
    comment: str | None = None
    enabled: bool = True
    id: int | None = None
    date_added: int | None = None
    date_modified: int | None = None


class Client(_Loose):
    client: str
    comment: str | None = None
    groups: list[int] = Field(default_factory=list)
    id: int | None = None
    name: str | None = None
    date_added: int | None = None
    date_modified: int | None = None


class QueryClient(_Loose):
    ip: str | None = None
    name: str | None = None


class QueryReply(_Loose):
    type: str | None = None
    time: float | None = None


class Query(_Loose):
    id: int | None = None
    time: float | None = None
    type: str | None = None
    domain: str | None = None
    cname: str | None = None
    status: str | None = None
    client: QueryClient | None = None
    dnssec: str | None = None
    reply: QueryReply | None = None
    list_id: int | None = None
    ttl: int | None = None
    upstream: str | None = None


class SystemInfo(_Loose):
    uptime: int | None = None
    memory: dict[str, Any] | None = None
    cpu: dict[str, Any] | None = None


class VersionInfo(_Loose):
    core: dict[str, Any] | None = None
    web: dict[str, Any] | None = None
    ftl: dict[str, Any] | None = None
    docker: dict[str, Any] | None = None


class NetworkDeviceIp(_Loose):
    ip: str
    name: str | None = None


class NetworkDevice(_Loose):
    id: int
    hwaddr: str | None = None
    interface: str | None = None
    firstSeen: int | None = None
    lastQuery: int | None = None
    numQueries: int | None = None
    macVendor: str | None = None
    ips: list[NetworkDeviceIp] = Field(default_factory=list)


class DhcpLease(_Loose):
    ip: str
    name: str | None = None
    hwaddr: str | None = None
    clientid: str | None = None
    expires: int | None = None


class Message(_Loose):
    id: int
    timestamp: float | None = None
    type: str | None = None
    plain: str | None = None
    html: str | None = None

"""Allow/deny domain rule tools (+ find_why_blocked composite)."""

from __future__ import annotations

from typing import Any, Literal

from fastmcp import FastMCP

from pihole_mcp.server import get_client
from pihole_mcp.util.validators import is_fqdn

DomainType = Literal["allow", "deny"]
DomainKind = Literal["exact", "regex"]


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def list_domain_rules(
        type: DomainType | None = None,
        kind: DomainKind | None = None,
        group: str | None = None,
        enabled: bool | None = None,
        cursor: int | None = None,
        limit: int = 100,
    ) -> dict:
        """List configured allow/deny rules. Filterable by type, kind, group, enabled."""
        limit = max(1, min(limit, 1000))
        return await get_client().list_domains(type=type, kind=kind, group=group, enabled=enabled, cursor=cursor, limit=limit)

    @mcp.tool
    async def get_domain_rule(type: DomainType, kind: DomainKind, domain: str) -> dict:
        """Look up a single domain rule by (type, kind, domain)."""
        return await get_client().get_domain(type, kind, domain)

    @mcp.tool
    async def block_domain(
        domain: str,
        kind: DomainKind = "exact",
        groups: list[int] | None = None,
        comment: str = "",
    ) -> dict:
        """Add a deny (block) rule. For kind='exact', domain must be a valid FQDN."""
        if kind == "exact" and not is_fqdn(domain):
            raise ValueError(f"{domain!r} is not a valid FQDN; use kind='regex' for patterns.")
        return await get_client().create_domain(
            "deny", kind, domain=domain, comment=comment or None, groups=groups, enabled=True,
        )

    @mcp.tool
    async def allow_domain(
        domain: str,
        kind: DomainKind = "exact",
        groups: list[int] | None = None,
        comment: str = "",
    ) -> dict:
        """Add an allow (whitelist) rule. For kind='exact', domain must be a valid FQDN."""
        if kind == "exact" and not is_fqdn(domain):
            raise ValueError(f"{domain!r} is not a valid FQDN; use kind='regex' for patterns.")
        return await get_client().create_domain(
            "allow", kind, domain=domain, comment=comment or None, groups=groups, enabled=True,
        )

    @mcp.tool
    async def update_domain_rule(
        type: DomainType,
        kind: DomainKind,
        domain: str,
        new_domain: str | None = None,
        comment: str | None = None,
        groups: list[int] | None = None,
        enabled: bool | None = None,
    ) -> dict:
        """Update an existing domain rule's fields."""
        fields: dict[str, Any] = {}
        if new_domain is not None:
            fields["domain"] = new_domain
        if comment is not None:
            fields["comment"] = comment
        if groups is not None:
            fields["groups"] = groups
        if enabled is not None:
            fields["enabled"] = enabled
        return await get_client().update_domain(type, kind, domain, **fields)

    @mcp.tool
    async def remove_domain_rule(
        type: DomainType,
        kind: DomainKind,
        domain: str,
        confirm: bool = False,
    ) -> dict:
        """Delete a single domain rule. Requires confirm=True."""
        if not confirm:
            raise ValueError("Set confirm=True to delete the rule.")
        await get_client().delete_domain(type, kind, domain)
        return {"deleted": {"type": type, "kind": kind, "domain": domain}}

    @mcp.tool
    async def batch_remove_domain_rules(items: list[dict], confirm: bool = False) -> dict:
        """Delete multiple domain rules in one call. items=[{type,kind,item}], requires confirm=True."""
        if not confirm:
            raise ValueError("Set confirm=True to batch-delete rules.")
        normalized = []
        for it in items:
            if "type" not in it or "kind" not in it or ("domain" not in it and "item" not in it):
                raise ValueError("Each item needs type, kind, and domain (or item).")
            normalized.append({"type": it["type"], "kind": it["kind"], "item": it.get("domain") or it["item"]})
        await get_client().batch_delete_domains(normalized)
        return {"deleted": normalized}

    @mcp.tool
    async def find_why_blocked(domain: str) -> dict:
        """Search gravity + adlists + rules for what would block this domain.

        Returns {blocked: bool, sources: [...], suggestion: str}.
        """
        result = await get_client().search(domain, n=20, partial=False)
        search = (result or {}).get("search") or {}
        domain_hits = search.get("domains") or []
        gravity_hits = search.get("gravity") or []
        sources: list[dict] = []
        for d in domain_hits:
            sources.append({"kind": "rule", "type": d.get("type"), "domain": d.get("domain"), "groups": d.get("groups"), "comment": d.get("comment")})
        for g in gravity_hits:
            sources.append({"kind": "adlist", "address": g.get("address"), "list_id": g.get("list_id") or (g.get("list") or {}).get("address"), "groups": g.get("group_ids")})
        blocked = bool(sources)
        suggestion = (
            "Add an allow_domain rule (type='allow', kind='exact') for the FQDN, "
            "scoped to your default group if you want global access."
            if blocked
            else "Domain is not in any of your blocklists; cause is elsewhere (router parental control, browser DoH, upstream resolver)."
        )
        return {"domain": domain, "blocked": blocked, "sources": sources, "suggestion": suggestion}

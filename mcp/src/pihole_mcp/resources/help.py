"""pihole://help/{topic} — embedded markdown help pages."""

from __future__ import annotations

from fastmcp import FastMCP

_TOPICS: dict[str, str] = {
    "getting_started": """# Getting Started

PiHoleMCP exposes the full Pi-hole v6 admin surface to AI clients (Claude, etc.) over MCP.

## Verify it works

1. Call `get_system_info` — should return version + uptime.
2. Call `get_blocking_status` — should return `enabled` or `disabled`.
3. Call `get_recent_blocked(limit=5)` — should return the 5 most recent blocked queries.

If any of these fail, check `pihole://help/troubleshooting`.

## Common workflows

- **Block a domain**: `block_domain(domain, kind='exact')`
- **Allow a domain**: `allow_domain(domain, kind='exact')`
- **Why is X blocked?**: `find_why_blocked(domain)`
- **Per-device rules**: see `pihole://help/per_device_rules`
- **Temporary unblock**: see `pihole://help/temp_allow`
""",

    "temp_allow": """# Temporary Allow Pattern

Use the `unblock_temporarily` prompt — it walks the agent through:

1. Identify what's blocking the target (calls `find_why_blocked`).
2. Add an `allow_domain` rule scoped to the right group(s).
3. Schedule auto-removal via JobTracker (background asyncio task).
4. Return job_id + cancel instructions.

Cancel an active temp-allow by deleting the rule directly with `remove_domain_rule`.
""",

    "per_device_rules": """# Per-Device Rules (Groups + Clients)

Pi-hole's per-device model:

- Each device is a **client** (identified by MAC / IP / hostname / `:interface`).
- Each client is assigned to one or more **groups**.
- Each **rule** (domain rule, adlist, regex) is scoped to one or more groups.
- A rule applies to a client iff the client and rule share a group.

## Add a new device to a restrictive group

```
# 1. Make the group if it doesn't exist
create_group(name='KidsTablet', enabled=True)

# 2. Register the device (MAC preferred — IPs change)
add_client(identifier='aa:bb:cc:dd:ee:ff', groups=[<KidsTablet_id>])

# 3. Scope adlists / domain rules to that group
update_adlist(url='https://...', groups=[<KidsTablet_id>], type='block')
```

## Caveat: iOS / macOS Private Wi-Fi MAC rotation

iOS and macOS rotate the MAC per network with "Private Wi-Fi Address" enabled. If a device
falls back into the Default group unexpectedly, the MAC likely rotated. Fix:
- Disable Private Wi-Fi Address for your network in the device's Wi-Fi settings, or
- Update the client with the new MAC: `update_client(client=<old_mac>, new_identifier=<new_mac>)`.
""",

    "troubleshooting": """# Troubleshooting

## 401 from MCP server
Token mismatch. Re-paste the bearer token from /etc/pihole-mcp/token.

## 403 / "origin not allowed"
Check `MCP_ALLOWED_ORIGINS` env. For browser clients add the origin; for curl, no Origin
header is sent (passes through).

## Pi-hole 429 `no_free_seats`
Too many concurrent API consumers on Pi-hole. Check the Pi-hole web UI (Settings → API → Sessions)
and kill stale sessions, or raise `webserver.api.max_sessions`.

## Pi-hole 403 on gravity/restart
`webserver.api.allow_destructive=false`. Re-run `install.sh` or set
`set_config(path='webserver.api.allow_destructive', value=True, confirm=True)` — though that
path is on the blocked-config allowlist, so you must do it via the Pi-hole web UI or shell.

## Tool result has `isError=true`
That's an expected tool-level error (bad args, validation failure). Read the message and adjust.

## gravity update times out
Don't call `run_gravity_update` and wait synchronously — it returns a `job_id`. Poll
`get_gravity_status(job_id)` until status='done'.

## Pi-hole upgrades broke MCP
Run `~/upgrade.sh` (pip install --upgrade pihole-mcp + systemctl restart pihole-mcp). The
Pi-hole upgrade itself doesn't touch us, but the API surface occasionally shifts.
""",
}


def register(mcp: FastMCP) -> None:
    @mcp.resource("pihole://help/{topic}")
    async def help_page(topic: str) -> dict:
        """Return embedded markdown help for one of: getting_started, temp_allow, per_device_rules, troubleshooting."""
        content = _TOPICS.get(topic)
        if content is None:
            return {"error": f"unknown topic {topic!r}", "available": sorted(_TOPICS)}
        return {"topic": topic, "content": content}

# PiHoleMCP

**Remote MCP server that wraps Pi-hole v6 so any MCP client (Claude Desktop,
Claude.ai, Cursor, etc.) can manage your Pi-hole as a custom connector.**

Install Pi-hole + the MCP server + a Caddy reverse proxy with one command. The
endpoint at `http://<pi-ip>/mcp` exposes ~55 tools covering DNS blocking,
domain rules, groups, clients, query log, stats, gravity, config, backup, and
everything else the Pi-hole REST API offers — with input validation, audit
logging, rate limits, and double-confirmation on destructive actions.

## Why

If you've ever found yourself SSH'd into a Pi-hole, copy-pasting heredoc
scripts and `sqlite3` SQL just to "unblock YouTube for two hours" or "move
the iPad into a stricter group," this is for you. PiHoleMCP turns the same
operations into MCP tool calls your AI assistant can execute on your behalf,
with the same audit trail and the same safety rails you'd hand-build into a
script.

## Install (one command)

```sh
curl -sSL https://raw.githubusercontent.com/EthanOrr930/PiHoleMCP/main/install.sh | sudo bash
```

What it does:

1. Installs Pi-hole v6 (if not already installed) via the official `install.pi-hole.net` script.
2. Shifts Pi-hole's web admin to internal port `8081`.
3. Creates a `pihole-mcp` system user, installs the MCP server into `/opt/pihole-mcp/venv`.
4. Generates a 32-byte bearer token (printed at the end).
5. Installs a systemd unit (`pihole-mcp.service`) that runs the MCP server.
6. Installs Caddy and writes a reverse proxy that maps `/mcp` → MCP server and `/admin` → Pi-hole.
7. Prints the connection info.

Total runtime: ~5 minutes on Pi 4 / ~15 minutes on Pi Zero W.

### Flags

- `--unattended` (requires `PIHOLE_APP_PASSWORD` env)
- `--mcp-port=N` (default 8473)
- `--no-caddy` (skip the reverse proxy; wire your own)
- `--tailscale-funnel` (set up `tailscale funnel 80` after install)
- `--tls=HOSTNAME` (Caddy auto-Let's Encrypt cert)
- `--docker` (use Docker compose path)
- `--local` (install from this checked-out repo)

See `docs/tls.md` for TLS setup paths.

## Connect from Claude

```
URL:   http://<pi-ip>/mcp     (or https://<tailscale-host>.ts.net/mcp)
Auth:  Bearer <token-from-install-output>
```

Settings → Connectors → Add custom connector. Full walkthrough in
`docs/connect-claude.md`.

## Architecture

```
+----------+    https     +-------------------+
|  Claude  | ───────────► |  Caddy   :80/:443 |
+----------+              +---------+---------+
                                    │
                  /mcp ─────────────┤────────── /admin , /api
                                    │
                  ┌─────────────────┴───────────────┐
                  ▼                                 ▼
        +--------------------+         +-----------------------+
        | PiHoleMCP :8473    |◄──REST──+ Pi-hole web :8081     |
        | (FastMCP + Python) |         |  FTL DNS  :53         |
        +--------------------+         +-----------------------+
```

The MCP server is a sidecar to Pi-hole on the same host — talks to FTL's REST
API over loopback (`127.0.0.1`) so session IDs are stable and there's no TLS to
manage internally. Caddy is the single public face.

## Tool count

| Category | Tools |
|---|---|
| DNS blocking | 3 |
| Domain rules | 8 |
| Adlists | 7 |
| Groups | 7 |
| Clients | 7 |
| Query log | 4 |
| Stats | 6 |
| History | 2 |
| Network + DHCP | 6 |
| System + actions | 11 |
| Config | 4 |
| Logs | 3 |
| Teleporter | 2 |
| Messages | 3 |
| Resources | 4 |
| Prompts | 5 |

Full reference: `docs/tools.md`. Pi-hole endpoint mapping: `docs/api-mapping.md`.

## Security model

- **Bearer token** (32 random bytes) generated at install; required on every request.
- **Origin header allowlist** (DNS-rebinding defense — `MCP_ALLOWED_ORIGINS`).
- **Per-tool rate limits** (60/min default; tighter for `restart_dns`, `flush_dns_logs`, `import_backup`).
- **Input validation** — FQDN regex, URL allowlist, MAC normalization, duration caps.
- **`confirm=True` required on every destructive tool**. `import_backup`
  requires an additional typed phrase `RESTORE PIHOLE`.
- **Config write allowlist** — `set_config` refuses to touch `webserver.api.*`,
  `database.*`, `dns.port`, `files.*`, `debug.*` (would lock the user out).
- **Audit log** — every tool call logged JSON to `/var/log/pihole-mcp/audit.log`
  with sensitive params redacted.
- **systemd hardening** — `ProtectSystem=strict`, `NoNewPrivileges`,
  `CapabilityBoundingSet=`, dropped privs to `pihole-mcp` user.

## Requirements

- Raspberry Pi (or x86 Debian/Ubuntu/Fedora) running Pi-hole v6.
- Python 3.11+.
- Port 80 free on the Pi (Caddy will bind it).
- ~50 MB RAM for the MCP server; ~30 MB for Caddy.

Pi Zero W is supported but slow — gravity updates take 20–40 minutes the first time.

## Development

```sh
git clone https://github.com/EthanOrr930/PiHoleMCP
cd PiHoleMCP/mcp
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

For a local install onto a Pi: `sudo bash install.sh --local` from the repo root.

## Status

Pre-1.0 / alpha. The tool surface and CLI are stable; the OAuth path is a future addition.

## License + acknowledgments

MIT.

Built on:
- [Pi-hole](https://pi-hole.net) — the whole reason this exists.
- [FastMCP](https://gofastmcp.com) — Python MCP server framework.
- [Model Context Protocol](https://modelcontextprotocol.io) — Anthropic's open spec.
- [Caddy](https://caddyserver.com) — the reverse proxy.

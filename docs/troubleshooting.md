# Troubleshooting

## Install issues

| Symptom | Fix |
|---|---|
| `Pi-hole config /etc/pihole/pihole.toml not found` | Pi-hole base install failed; check `journalctl -u pihole-FTL` and re-run `install.sh`. |
| `Port 80 already in use` | Another service holds port 80; stop it or re-run with `--no-caddy` and proxy yourself. |
| `PIHOLE_APP_PASSWORD is required in --unattended mode` | Export it: `PIHOLE_APP_PASSWORD=... sudo -E bash install.sh --unattended`. |
| ARM wheel build errors | Re-run with `--local` after `git clone` so pip can use piwheels (`extra-index-url https://www.piwheels.org/simple` is set automatically on armv6/v7). |

## Service status

```sh
systemctl status pihole-mcp caddy pihole-FTL
journalctl -u pihole-mcp -n 100 --no-pager
tail -F /var/log/pihole-mcp/audit.log
```

## Connection issues from Claude

| Symptom | Likely cause | Fix |
|---|---|---|
| `401 unauthorized` | Bearer token mismatch | Re-copy `cat /etc/pihole-mcp/token`, paste into Claude connector auth. |
| `403 forbidden — origin not allowed` | Browser Origin header rejected | Add origin to `MCP_ALLOWED_ORIGINS` env (comma-sep) or set `*` for testing. |
| `connection refused` | Service down | `systemctl start pihole-mcp` then check status. |
| `connection refused` to `/admin` only | Pi-hole web didn't re-bind to 8081 | `pihole-FTL --config webserver.port` to verify; should be `127.0.0.1:8081,[::1]:8081`. |
| Browser cert warning | Self-signed or no TLS | Use Tailscale Funnel (see `tls.md`) or `mcp-remote` shim (see `connect-claude.md`). |
| Tool calls silently hang | Caddy buffering SSE | Caddy default config in `install/Caddyfile` has `flush_interval -1` — make sure your override keeps it. |

## Pi-hole API errors surfaced as tool errors

| Pi-hole error | Tool result hint |
|---|---|
| 401 (after re-auth retry) | App password rejected. Regenerate via web UI → Settings → API → Create Application Password, then `set_config` won't help here — edit `/etc/pihole-mcp/.env` directly and `systemctl restart pihole-mcp`. |
| 403 destructive disabled | Pi-hole's `webserver.api.allow_destructive` is false. Edit via Pi-hole web UI: Settings → All settings → search `allow_destructive`, set true, save. |
| 429 generic | Pi-hole rate-limited us; back off. |
| 429 `no_free_seats` | Too many concurrent API sessions on Pi-hole. Web UI → Settings → API → Sessions; revoke stale ones, OR raise `webserver.api.max_sessions`. |
| `InvalidRegex` | Your regex didn't compile in Pi-hole; check the pattern. |

## Per-tool gotchas

- **`run_gravity_update`** returns a `job_id` immediately. Do NOT wait — poll
  `get_gravity_status(job_id)` until `status == "done"`. On Pi Zero W gravity
  takes 20–40 minutes the first time.
- **`tail_queries`** is hard-capped at 1000 rows server-side regardless of
  `limit`. Paginate with `since_cursor`.
- **`set_blocking(enabled=False)`** requires `duration_seconds` — there is no
  "disable forever" path. Use `set_config(path='dns.blocking', value=False)`
  if you really mean permanent (it's NOT on the blocked-config allowlist).
- **`set_config`** refuses writes to `webserver.api.*`, `database.*`,
  `dns.port`, `files.*`, `debug.*`. Edit the Pi-hole web UI directly for
  those — we won't help you lock yourself out.
- **`import_backup`** requires both `confirm=True` AND
  `confirmation_phrase="RESTORE PIHOLE"`. Intentional friction.

## After a Pi-hole upgrade

```sh
sudo bash /opt/pihole-mcp/upgrade.sh
```

If the Pi-hole REST schema changed in a way that breaks us, please open an issue
with `pihole -v` output and a couple of failing tool calls from the audit log.

## Total reset (without losing Pi-hole)

```sh
sudo bash /Users/ethanorr/Documents/projects/PiHoleMCP/uninstall.sh   # MCP only
sudo bash /Users/ethanorr/Documents/projects/PiHoleMCP/install.sh
```

Pi-hole itself is never touched by `uninstall.sh`.

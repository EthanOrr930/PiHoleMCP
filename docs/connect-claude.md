# Connect from Claude

PiHoleMCP exposes a standard remote MCP endpoint at `http(s)://<pi-ip>/mcp`. Any
MCP-compatible client works — Claude Desktop, Claude.ai, Cursor, IDE extensions.

## Claude Desktop / Claude.ai

1. Open **Claude Desktop** or **claude.ai**.
2. Settings → **Connectors** → **Add custom connector**.
3. Fill in:
   - **URL**: `http://<pi-ip>/mcp` (substitute the actual LAN IP, e.g. `http://192.168.0.60/mcp`).
   - **Auth header**: `Authorization: Bearer <token>` — the token printed at the end of `install.sh` (also in `/etc/pihole-mcp/token`).
4. Save. Refresh the connectors list.
5. PiHoleMCP appears with ~55 tools available (DNS control, domains, groups, clients, query log, stats, etc.).

## HTTPS strongly recommended

Bearer tokens over HTTP work but expose the token to any sniffer on the LAN. See `tls.md`
for three setup paths (Tailscale Funnel, Cloudflare Tunnel, Caddy + Let's Encrypt).

## Self-signed cert / LAN-only via `mcp-remote` shim

Claude rejects self-signed certs directly. Use [`mcp-remote`](https://github.com/geelen/mcp-remote)
to bridge:

```json
{
  "mcpServers": {
    "pihole": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "https://pi-hole.local:8473/mcp",
        "--allow-http",
        "--header", "Authorization:${PIHOLE_MCP_TOKEN}"
      ],
      "env": { "PIHOLE_MCP_TOKEN": "Bearer <token>" }
    }
  }
}
```

(Drop into `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS.)

## Verifying without Claude

```sh
curl -sS -H "Authorization: Bearer <token>" \
     -H "MCP-Protocol-Version: 2025-06-18" \
     -H "Accept: application/json, text/event-stream" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","clientInfo":{"name":"curl","version":"0"},"capabilities":{}}}' \
     http://<pi-ip>/mcp
```

Returns an InitializeResult JSON if everything's wired up.

Or use the MCP Inspector:

```sh
npx @modelcontextprotocol/inspector http://<pi-ip>/mcp
```

Then point Inspector at the URL with your bearer token in the headers field.

## Troubleshooting

| Symptom | Likely fix |
|---|---|
| `401 unauthorized` | Wrong / missing bearer token. Re-copy from `/etc/pihole-mcp/token`. |
| `403 forbidden` | `MCP_ALLOWED_ORIGINS` rejects your browser's Origin header. Add it or set `*` for testing. |
| `connection refused` | Caddy / pihole-mcp service not running. `systemctl status pihole-mcp caddy`. |
| Tool returns `isError: true` with helpful message | Expected for bad args — read the message. |
| Cert warning in browser | Use HTTPS path (Tailscale Funnel etc.) or `mcp-remote` shim. |

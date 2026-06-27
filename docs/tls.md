# TLS for PiHoleMCP

Three real options, ranked by ease + suitability for a home Pi behind NAT.

## Option A — Tailscale Funnel (recommended)

Zero router config, automatic Let's Encrypt cert, works from anywhere on the
internet via your private tailnet hostname.

```sh
# On the Pi
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
sudo tailscale funnel 80    # exposes Caddy on the Pi to your tailnet's funnel domain
```

The resulting URL is something like `https://pihole.<your-tailnet>.ts.net/mcp`.

Pros: free for personal use, real TLS, no port forwarding, no domain needed.
Cons: requires a Tailscale account.

## Option B — Cloudflare Tunnel

If you have a Cloudflare account + a domain:

```sh
# On the Pi
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 \
     -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
cloudflared tunnel login
cloudflared tunnel create pihole-mcp
cloudflared tunnel route dns pihole-mcp pihole.<your-domain>.com
cloudflared tunnel run pihole-mcp     # systemd unit if you want it persistent
```

`config.yml` for the tunnel:

```yaml
tunnel: <your-tunnel-uuid>
credentials-file: /root/.cloudflared/<uuid>.json
ingress:
  - hostname: pihole.<your-domain>.com
    service: http://localhost:80
  - service: http_status:404
```

Optionally layer **Cloudflare Access** on top for OAuth (no code changes needed on
our end; we just don't add bearer auth in front of an Access-protected origin).

## Option C — Caddy + Let's Encrypt direct

Requires ports 80 and 443 open from the public internet to your Pi, or DNS-01
challenge if you're behind NAT.

Re-run the installer with `--tls=<hostname>`:

```sh
sudo bash install.sh --tls=pihole.example.com
```

This swaps `install/Caddyfile` for `install/Caddyfile.tls` with `${HOSTNAME}`
substituted. Caddy handles ACME challenge + auto-renewal.

For DNS-01 challenge (behind NAT, no inbound 80/443): use one of Caddy's
[DNS provider modules](https://github.com/caddy-dns) — install the matching
caddy-dns binary, then add the `dns <provider>` directive inside the `tls`
block.

## LAN-only (no TLS)

Works fine for testing. Caveats:
- Bearer token is sent in cleartext — anyone sniffing your Wi-Fi sees it.
- Claude rejects self-signed HTTPS, so don't even bother with one — use plain HTTP and the [`mcp-remote`](https://github.com/geelen/mcp-remote) shim with `--allow-http`. See `connect-claude.md`.

## Test that TLS terminates correctly

```sh
curl -v -H "Authorization: Bearer <token>" \
     -H "MCP-Protocol-Version: 2025-06-18" \
     -H "Accept: application/json, text/event-stream" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","clientInfo":{"name":"curl","version":"0"},"capabilities":{}}}' \
     https://<hostname>/mcp
```

You want `HTTP/2 200` (or `HTTP/1.1 200`) + a valid TLS handshake, no cert
warnings in verbose output.

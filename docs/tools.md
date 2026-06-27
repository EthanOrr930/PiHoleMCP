# Tool reference

PiHoleMCP exposes ~55 tools organized by category. Every tool is also a method
on the Pi-hole v6 REST API; see `api-mapping.md` for the 1:1 mapping.

Destructive tools require `confirm=True`. The most destructive (`import_backup`)
requires an additional typed phrase. Rate limits apply per tool — see
`mcp/src/pihole_mcp/middleware/rate_limit.py`.

## DNS blocking (3)

| Tool | Description |
|---|---|
| `get_blocking_status()` | Current status + remaining disable timer |
| `set_blocking(enabled, duration_seconds?, confirm)` | Enable/disable; duration REQUIRED when disabling |
| `pause_blocking(duration_seconds)` | Disable for 10..86400 seconds |

## Domain rules (8)

| Tool | Description |
|---|---|
| `list_domain_rules(type?, kind?, group?, enabled?, cursor?, limit)` | Paginated rule list |
| `get_domain_rule(type, kind, domain)` | Fetch single rule |
| `block_domain(domain, kind, groups, comment)` | Add deny rule (FQDN validated for exact kind) |
| `allow_domain(domain, kind, groups, comment)` | Add allow rule |
| `update_domain_rule(type, kind, domain, ...)` | Edit fields |
| `remove_domain_rule(type, kind, domain, confirm)` | Delete one rule |
| `batch_remove_domain_rules(items, confirm)` | Bulk delete |
| `find_why_blocked(domain)` | Composite — searches gravity + rules, suggests fix |

## Adlists (7)

| Tool | Description |
|---|---|
| `list_adlists(type?, cursor?, limit?)` | All configured adlists |
| `get_adlist(url)` | Single adlist |
| `add_adlist(url, type, groups, comment, enabled)` | Subscribe new (URL validated) |
| `update_adlist(url, ...)` | Edit fields |
| `toggle_adlist(url, enabled, type)` | Enable/disable |
| `remove_adlist(url, type, confirm)` | Unsubscribe |
| `batch_remove_adlists(items, confirm)` | Bulk unsubscribe |

## Groups (7)

| Tool | Description |
|---|---|
| `list_groups()` | All groups |
| `get_group(name)` | Single group |
| `create_group(name, comment, enabled)` | Create |
| `update_group(name, ...)` | Rename / edit |
| `toggle_group(name, enabled)` | Enable/disable |
| `delete_group(name, confirm)` | Delete |
| `batch_delete_groups(names, confirm)` | Bulk delete |

## Clients (7)

| Tool | Description |
|---|---|
| `list_clients()` | Configured clients |
| `list_unconfigured_clients()` | Devices FTL has seen, no group yet |
| `get_client_detail(client)` | Single client by identifier |
| `add_client(identifier, groups, comment)` | Register (IP/MAC/host/`:iface`) |
| `update_client(client, ...)` | Edit |
| `remove_client(client, confirm)` | Delete |
| `batch_remove_clients(clients, confirm)` | Bulk delete |

## Query log (4)

| Tool | Description |
|---|---|
| `tail_queries(since_cursor?, limit, ...filters)` | Server caps limit at 1000 |
| `get_query_filter_suggestions()` | Valid filter values |
| `get_recent_blocked(limit)` | Most recent blocked queries (max 100) |
| `search_domain_in_lists(domain, n, partial)` | Search adlists + rules |

## Stats (6)

| Tool | Description |
|---|---|
| `get_stats_summary(source, from_ts, until_ts)` | Headline numbers |
| `get_top_domains(source, blocked, limit, ...)` | Top domains |
| `get_top_clients(source, blocked, limit, ...)` | Top clients |
| `get_upstreams(source, ...)` | Upstream resolver breakdown |
| `get_query_types(source, ...)` | A / AAAA / HTTPS / etc. |
| `get_db_content_summary(from_ts, until_ts)` | Database metadata |

## History (2)

| Tool | Description |
|---|---|
| `get_activity_graph(source, from_ts, until_ts)` | Time-series |
| `get_clients_activity(source, n, ...)` | Per-client time-series |

## Network + DHCP (6)

| Tool | Description |
|---|---|
| `list_network_devices()` | All LAN devices FTL has seen |
| `get_network_gateway()` | Gateway + interface |
| `remove_network_device(device_id, confirm)` | Forget a device |
| `flush_arp_cache(confirm)` | Clear ARP/network table |
| `list_dhcp_leases()` | DHCP leases |
| `revoke_dhcp_lease(ip, confirm)` | Revoke one |

## System + actions (10)

| Tool | Description |
|---|---|
| `get_system_info()` | Composite: version + system + host + FTL |
| `get_version_info()` | Just versions |
| `get_ftl_info()` | FTL runtime |
| `get_host_info()` | OS / kernel |
| `get_metrics()` | Prometheus-style |
| `get_sensors_info()` | CPU temp |
| `get_database_info()` | DB stats |
| `run_gravity_update(confirm)` | Async job; returns `job_id` |
| `get_gravity_status(job_id)` | Poll progress |
| `restart_dns(confirm)` | Restart FTL |
| `flush_dns_logs(confirm)` | Clear live query log |

## Config (4)

| Tool | Description |
|---|---|
| `get_config(path?, detailed?)` | Read |
| `list_config_keys()` | Full key tree |
| `set_config(path, value, confirm)` | Write (refuses blocked paths) |
| `reset_config_value(path, value, confirm)` | Remove from arrays |

## Logs (3)

| Tool | Description |
|---|---|
| `tail_log_dnsmasq(next_id?)` | DNS log |
| `tail_log_ftl(next_id?)` | FTL daemon log |
| `tail_log_webserver(next_id?)` | Embedded webserver log |

## Teleporter (2)

| Tool | Description |
|---|---|
| `export_backup()` | Returns base64 zip + sha256 |
| `import_backup(data_b64, confirm, confirmation_phrase)` | Restore — DOUBLE confirmation |

## Messages (3)

| Tool | Description |
|---|---|
| `get_messages()` | All diagnostic messages |
| `get_messages_count()` | Just the count |
| `delete_message(message_id, confirm)` | Dismiss one |

## Resources

| URI | Description |
|---|---|
| `pihole://overview` | Live dashboard (30s cache) |
| `pihole://recent_changes` | Last 100 audit log entries |
| `pihole://topology` | Groups + clients + rule counts (60s cache) |
| `pihole://help/{topic}` | `getting_started` / `temp_allow` / `per_device_rules` / `troubleshooting` |

## Prompts (slash commands)

| Name | Description |
|---|---|
| `/investigate_block <domain>` | Walks through diagnosis + proposes a fix |
| `/daily_summary` | Today's stats roll-up |
| `/audit_blocklists` | Identify stale adlists |
| `/unblock_temporarily <domain> <minutes>` | Targeted reversible allow |
| `/lockdown_device <client> <level>` | Move device to restrictive group |

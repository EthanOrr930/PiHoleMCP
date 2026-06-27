# Pi-hole REST endpoint → MCP tool mapping

Every Pi-hole v6 REST endpoint is reachable through one or more MCP tools.
Endpoints not exposed (auth, internal SID lifecycle) are noted explicitly.

| Pi-hole endpoint | MCP tool(s) |
|---|---|
| `POST /api/auth` | (internal — `SessionManager` handles SID) |
| `GET /api/auth` | (internal — exposed indirectly via tool errors) |
| `DELETE /api/auth` | (internal — fires on server shutdown) |
| `GET /api/dns/blocking` | `get_blocking_status` |
| `POST /api/dns/blocking` | `set_blocking`, `pause_blocking` |
| `GET /api/domains` | `list_domain_rules` |
| `GET /api/domains/{type}/{kind}/{domain}` | `get_domain_rule` |
| `POST /api/domains/{type}/{kind}` | `block_domain`, `allow_domain` |
| `PUT /api/domains/{type}/{kind}/{domain}` | `update_domain_rule` |
| `DELETE /api/domains/{type}/{kind}/{domain}` | `remove_domain_rule` |
| `POST /api/domains:batchDelete` | `batch_remove_domain_rules` |
| `GET /api/lists` | `list_adlists` |
| `GET /api/lists/{url}` | `get_adlist` |
| `POST /api/lists` | `add_adlist` |
| `PUT /api/lists/{url}` | `update_adlist`, `toggle_adlist` |
| `DELETE /api/lists/{url}` | `remove_adlist` |
| `POST /api/lists:batchDelete` | `batch_remove_adlists` |
| `GET /api/groups` | `list_groups` |
| `GET /api/groups/{name}` | `get_group` |
| `POST /api/groups` | `create_group` |
| `PUT /api/groups/{name}` | `update_group`, `toggle_group` |
| `DELETE /api/groups/{name}` | `delete_group` |
| `POST /api/groups:batchDelete` | `batch_delete_groups` |
| `GET /api/clients` | `list_clients` |
| `GET /api/clients/_suggestions` | `list_unconfigured_clients` |
| `GET /api/clients/{client}` | `get_client_detail` |
| `POST /api/clients` | `add_client` |
| `PUT /api/clients/{client}` | `update_client` |
| `DELETE /api/clients/{client}` | `remove_client` |
| `POST /api/clients:batchDelete` | `batch_remove_clients` |
| `GET /api/queries` | `tail_queries` |
| `GET /api/queries/suggestions` | `get_query_filter_suggestions` |
| `GET /api/stats/recent_blocked` | `get_recent_blocked` |
| `GET /api/search/{domain}` | `search_domain_in_lists`, `find_why_blocked` (composite) |
| `GET /api/stats/summary` | `get_stats_summary(source="live")` |
| `GET /api/stats/database/summary` | `get_stats_summary(source="database")` |
| `GET /api/stats/top_domains` | `get_top_domains(source="live")` |
| `GET /api/stats/database/top_domains` | `get_top_domains(source="database")` |
| `GET /api/stats/top_clients` | `get_top_clients(source="live")` |
| `GET /api/stats/database/top_clients` | `get_top_clients(source="database")` |
| `GET /api/stats/upstreams` | `get_upstreams(source="live")` |
| `GET /api/stats/database/upstreams` | `get_upstreams(source="database")` |
| `GET /api/stats/query_types` | `get_query_types(source="live")` |
| `GET /api/stats/database/query_types` | `get_query_types(source="database")` |
| `GET /api/stats/database/content` | `get_db_content_summary` |
| `GET /api/history` | `get_activity_graph(source="live")` |
| `GET /api/history/database` | `get_activity_graph(source="database")` |
| `GET /api/history/clients` | `get_clients_activity(source="live")` |
| `GET /api/history/database/clients` | `get_clients_activity(source="database")` |
| `GET /api/network/devices` | `list_network_devices` |
| `GET /api/network/gateway` | `get_network_gateway` |
| `DELETE /api/network/devices/{id}` | `remove_network_device` |
| `GET /api/dhcp/leases` | `list_dhcp_leases` |
| `DELETE /api/dhcp/leases/{ip}` | `revoke_dhcp_lease` |
| `GET /api/config` | `get_config`, `list_config_keys` |
| `GET /api/config/{element-path}` | `get_config(path=...)` |
| `PATCH /api/config` | `set_config` |
| `DELETE /api/config/{element-path}/{value}` | `reset_config_value` |
| `PUT /api/config/{element-path}/{value}` | (not surfaced — use `set_config`) |
| `GET /api/info/version` | `get_version_info`, `get_system_info` (composite) |
| `GET /api/info/system` | `get_system_info` (composite) |
| `GET /api/info/host` | `get_host_info`, `get_system_info` |
| `GET /api/info/ftl` | `get_ftl_info`, `get_system_info` |
| `GET /api/info/sensors` | `get_sensors_info` |
| `GET /api/info/login` | (not exposed — internal) |
| `GET /api/info/metrics` | `get_metrics` |
| `GET /api/info/database` | `get_database_info` |
| `GET /api/info/client` | (not exposed — reveals connection internals) |
| `GET /api/info/messages` | `get_messages` |
| `GET /api/info/messages/count` | `get_messages_count` |
| `DELETE /api/info/messages/{id}` | `delete_message` |
| `POST /api/action/gravity` | `run_gravity_update` (async job) |
| `POST /api/action/restartdns` | `restart_dns` |
| `POST /api/action/flush/logs` | `flush_dns_logs` |
| `POST /api/action/flush/arp` | `flush_arp_cache` |
| `GET /api/logs/dnsmasq` | `tail_log_dnsmasq` |
| `GET /api/logs/ftl` | `tail_log_ftl` |
| `GET /api/logs/webserver` | `tail_log_webserver` |
| `GET /api/teleporter` | `export_backup` |
| `POST /api/teleporter` | `import_backup` (double confirmation) |
| `GET /api/endpoints` | (not exposed — meta-introspection unused at tool layer) |
| `GET /api/docs` | (not exposed — Pi-hole's own Swagger UI at `/admin`) |

#!/usr/bin/env bash
# Called by install.sh AFTER Pi-hole base install is healthy.
# Re-ports Pi-hole web to 8081, enables destructive API actions, captures
# an application password into /etc/pihole-mcp/.env.
set -euo pipefail

PIHOLE_TOML="/etc/pihole/pihole.toml"
MCP_ENV_DIR="/etc/pihole-mcp"
MCP_ENV_FILE="${MCP_ENV_DIR}/.env"
MCP_USER="pihole-mcp"

require_root() {
  if [[ ${EUID} -ne 0 ]]; then
    echo "post-install.sh must run as root." >&2
    exit 1
  fi
}

shift_pihole_web_port() {
  if [[ ! -f "${PIHOLE_TOML}" ]]; then
    echo "Pi-hole config ${PIHOLE_TOML} not found. Aborting." >&2
    exit 1
  fi
  echo "==> Shifting Pi-hole web server to port 8081 (frees :80 for Caddy)..."
  pihole-FTL --config webserver.port '127.0.0.1:8081,[::1]:8081' >/dev/null
  systemctl restart pihole-FTL >/dev/null 2>&1 || true
  sleep 2
}

enable_destructive_actions() {
  echo "==> Enabling Pi-hole webserver.api.allow_destructive ..."
  pihole-FTL --config webserver.api.allow_destructive true >/dev/null
}

reload_pihole() {
  echo "==> Reloading Pi-hole..."
  pihole reloaddns >/dev/null || true
  systemctl restart pihole-FTL || true
}

ensure_env_file() {
  mkdir -p "${MCP_ENV_DIR}"
  chmod 750 "${MCP_ENV_DIR}"
  touch "${MCP_ENV_FILE}"
  chmod 600 "${MCP_ENV_FILE}"
  chown "${MCP_USER}":"${MCP_USER}" "${MCP_ENV_DIR}" "${MCP_ENV_FILE}" 2>/dev/null || true
}

capture_app_password() {
  local pw="${PIHOLE_APP_PASSWORD:-}"
  if [[ -z "${pw}" ]]; then
    if [[ "${PIHOLEMCP_UNATTENDED:-0}" == "1" ]]; then
      echo "PIHOLE_APP_PASSWORD is required in --unattended mode." >&2
      exit 1
    fi
    cat <<EOF
==> Generate a Pi-hole Application Password:
    1. Open http://$(hostname -I | awk '{print $1}'):8081/admin in a browser.
    2. Sign in with your Pi-hole web password.
    3. Settings → API → Create application password → copy it.

EOF
    read -rsp "Paste application password: " pw
    echo
  fi
  printf 'PIHOLE_URL=http://127.0.0.1:8081\nPIHOLE_APP_PASSWORD=%s\n' "${pw}" > "${MCP_ENV_FILE}"
  chmod 600 "${MCP_ENV_FILE}"
  chown "${MCP_USER}":"${MCP_USER}" "${MCP_ENV_FILE}" 2>/dev/null || true
}

main() {
  require_root
  shift_pihole_web_port
  enable_destructive_actions
  reload_pihole
  ensure_env_file
  capture_app_password
  echo "==> Pi-hole post-install complete."
}

main "$@"

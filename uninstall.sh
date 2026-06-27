#!/usr/bin/env bash
# Remove PiHoleMCP. Pi-hole itself is NOT touched.
set -euo pipefail

MCP_USER="pihole-mcp"
MCP_PREFIX="/opt/pihole-mcp"
MCP_CONFIG_DIR="/etc/pihole-mcp"
MCP_LOG_DIR="/var/log/pihole-mcp"
SYSTEMD_UNIT="/etc/systemd/system/pihole-mcp.service"

PURGE=0
KEEP_CADDY=1
for arg in "$@"; do
  case "${arg}" in
    --purge) PURGE=1 ;;
    --remove-caddy) KEEP_CADDY=0 ;;
    -h|--help)
      cat <<EOF
Usage: sudo bash uninstall.sh [--purge] [--remove-caddy]
  --purge          Also delete logs in ${MCP_LOG_DIR}.
  --remove-caddy   Remove Caddy and its config too.
EOF
      exit 0
      ;;
    *) echo "Unknown flag: ${arg}" >&2; exit 1 ;;
  esac
done

[[ ${EUID} -eq 0 ]] || { echo "Run as root." >&2; exit 1; }

echo "==> Stopping pihole-mcp..."
systemctl disable --now pihole-mcp.service 2>/dev/null || true
rm -f "${SYSTEMD_UNIT}"
systemctl daemon-reload

echo "==> Removing venv + config dirs..."
rm -rf "${MCP_PREFIX}" "${MCP_CONFIG_DIR}"

if [[ ${PURGE} -eq 1 ]]; then
  echo "==> Purging logs in ${MCP_LOG_DIR}..."
  rm -rf "${MCP_LOG_DIR}"
else
  echo "==> Keeping logs in ${MCP_LOG_DIR} (use --purge to remove)."
fi

echo "==> Removing system user ${MCP_USER}..."
userdel "${MCP_USER}" 2>/dev/null || true

rm -f /etc/logrotate.d/pihole-mcp

if [[ ${KEEP_CADDY} -eq 0 ]]; then
  echo "==> Removing Caddy..."
  if command -v apt-get >/dev/null 2>&1; then
    apt-get -y remove --purge caddy || true
  elif command -v dnf >/dev/null 2>&1; then
    dnf -y remove caddy || true
  fi
  rm -f /etc/caddy/Caddyfile
fi

echo "==> Done. Pi-hole itself is untouched."

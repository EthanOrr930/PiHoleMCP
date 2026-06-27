#!/usr/bin/env bash
# In-place upgrade — pip install --upgrade and restart the systemd unit.
set -euo pipefail

MCP_USER="pihole-mcp"
MCP_VENV="/opt/pihole-mcp/venv"
REPO_URL="https://github.com/EthanOrr930/PiHoleMCP"
REPO_BRANCH="${PIHOLEMCP_BRANCH:-main}"

[[ ${EUID} -eq 0 ]] || { echo "Run as root." >&2; exit 1; }

echo "==> Upgrading pihole-mcp from ${REPO_URL}@${REPO_BRANCH}..."
sudo -u "${MCP_USER}" "${MCP_VENV}/bin/pip" install -U \
  "git+${REPO_URL}.git@${REPO_BRANCH}#subdirectory=mcp"

echo "==> Restarting service..."
systemctl restart pihole-mcp
sleep 1
systemctl --no-pager status pihole-mcp | head -10
echo "==> Upgrade complete."

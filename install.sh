#!/usr/bin/env bash
# PiHoleMCP — single-shot installer.
# Installs Pi-hole v6 (if missing) + this MCP server + Caddy reverse proxy
# so http://<pi-ip>/mcp serves the MCP endpoint and http://<pi-ip>/admin
# serves the Pi-hole web UI.
set -euo pipefail

VERSION="0.1.0"
REPO_URL="https://github.com/EthanOrr930/PiHoleMCP"
REPO_BRANCH="${PIHOLEMCP_BRANCH:-main}"
MCP_USER="pihole-mcp"
MCP_PREFIX="/opt/pihole-mcp"
MCP_VENV="${MCP_PREFIX}/venv"
MCP_CONFIG_DIR="/etc/pihole-mcp"
MCP_LOG_DIR="/var/log/pihole-mcp"
MCP_TOKEN_FILE="${MCP_CONFIG_DIR}/token"
MCP_ENV_FILE="${MCP_CONFIG_DIR}/.env"
SYSTEMD_UNIT="/etc/systemd/system/pihole-mcp.service"

MCP_PORT=8473
INSTALL_CADDY=1
INSTALL_TS_FUNNEL=0
TLS_HOSTNAME=""
USE_DOCKER=0
UNATTENDED=0
LOCAL_INSTALL=0

color() { printf '\033[%sm%s\033[0m\n' "$1" "$2"; }
info()  { color "1;36" "==> $*"; }
warn()  { color "1;33" "WARN: $*" >&2; }
die()   { color "1;31" "ERR: $*" >&2; exit 1; }

usage() {
  cat <<EOF
PiHoleMCP installer v${VERSION}

Usage: sudo bash install.sh [flags]

Flags:
  --unattended            Skip prompts; requires PIHOLE_APP_PASSWORD env.
  --mcp-port=N            Override MCP listen port (default ${MCP_PORT}).
  --no-caddy              Skip Caddy reverse proxy install.
  --tailscale-funnel      After install, run \`tailscale funnel 80\`.
  --tls=HOSTNAME          Use Caddy auto-TLS for HOSTNAME (Let's Encrypt).
  --docker                Use Docker compose install path instead of bare metal.
  --local                 Install from this checked-out repo (\$PWD), not GitHub.
  -h | --help             Show this help.

Environment:
  PIHOLE_APP_PASSWORD     Required with --unattended (Pi-hole Application Password).
  PIHOLEMCP_BRANCH        Git ref to pip-install from (default main).
EOF
}

parse_args() {
  for arg in "$@"; do
    case "${arg}" in
      --unattended)            UNATTENDED=1 ;;
      --mcp-port=*)            MCP_PORT="${arg#*=}" ;;
      --no-caddy)              INSTALL_CADDY=0 ;;
      --tailscale-funnel)      INSTALL_TS_FUNNEL=1 ;;
      --tls=*)                 TLS_HOSTNAME="${arg#*=}" ;;
      --docker)                USE_DOCKER=1 ;;
      --local)                 LOCAL_INSTALL=1 ;;
      -h|--help)               usage; exit 0 ;;
      *) die "Unknown flag: ${arg}" ;;
    esac
  done
}

require_root() {
  [[ ${EUID} -eq 0 ]] || die "Run as root (sudo bash install.sh ...)"
}

detect_os() {
  if [[ ! -r /etc/os-release ]]; then
    die "Cannot detect OS (/etc/os-release missing)."
  fi
  # shellcheck source=/dev/null
  . /etc/os-release
  case "${ID:-}${ID_LIKE:-}" in
    *debian*|*ubuntu*|*raspbian*) OS_FAMILY="debian" ;;
    *fedora*|*rhel*|*centos*)     OS_FAMILY="rhel" ;;
    *) die "Unsupported OS: ${ID:-unknown}. Use Debian / Ubuntu / Raspberry Pi OS / Fedora." ;;
  esac
  info "Detected OS family: ${OS_FAMILY} (${ID:-unknown})"
}

apt_install() {
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$@"
}

ensure_pkg() {
  if [[ "${OS_FAMILY}" == "debian" ]]; then
    apt-get update -qq
    apt_install "$@"
  else
    dnf install -y "$@"
  fi
}

pihole_installed() { [[ -f /etc/pihole/pihole.toml ]]; }

install_pihole() {
  if pihole_installed; then
    info "Pi-hole v6 already installed; skipping base install."
    return
  fi
  info "Installing Pi-hole v6 (this may take a while)..."
  if [[ ${UNATTENDED} -eq 1 ]]; then
    cp install/pihole-setup-vars.example /etc/pihole/setupVars.conf 2>/dev/null || true
    curl -sSL https://install.pi-hole.net | bash /dev/stdin --unattended
  else
    curl -sSL https://install.pi-hole.net | bash
  fi
  info "Pi-hole base install complete."
}

post_install_pihole() {
  info "Running Pi-hole post-install steps (port shift, allow_destructive, app password)..."
  if [[ -f install/post-install.sh ]]; then
    PIHOLEMCP_UNATTENDED="${UNATTENDED}" bash install/post-install.sh
  else
    die "install/post-install.sh missing — bad install tree."
  fi
}

create_user() {
  if id "${MCP_USER}" >/dev/null 2>&1; then
    info "User ${MCP_USER} already exists."
    return
  fi
  info "Creating system user ${MCP_USER}..."
  useradd --system --no-create-home --shell /usr/sbin/nologin --home "${MCP_PREFIX}" "${MCP_USER}"
}

ensure_dirs() {
  mkdir -p "${MCP_PREFIX}" "${MCP_CONFIG_DIR}" "${MCP_LOG_DIR}"
  chown -R "${MCP_USER}":"${MCP_USER}" "${MCP_PREFIX}" "${MCP_CONFIG_DIR}" "${MCP_LOG_DIR}"
  chmod 750 "${MCP_CONFIG_DIR}"
}

install_python_venv() {
  info "Installing Python 3.11+ + venv..."
  if [[ "${OS_FAMILY}" == "debian" ]]; then
    ensure_pkg python3 python3-venv python3-pip curl
  else
    ensure_pkg python3 python3-pip curl
  fi
  info "Creating venv at ${MCP_VENV}..."
  if [[ ! -d "${MCP_VENV}" ]]; then
    sudo -u "${MCP_USER}" python3 -m venv "${MCP_VENV}"
  fi
  local pip_args=()
  if [[ "$(uname -m)" =~ ^(armv6l|armv7l)$ ]]; then
    pip_args+=(--extra-index-url https://www.piwheels.org/simple)
  fi
  info "Installing PiHoleMCP into venv..."
  if [[ ${LOCAL_INSTALL} -eq 1 ]]; then
    sudo -u "${MCP_USER}" "${MCP_VENV}/bin/pip" install -U "${pip_args[@]}" "$(pwd)/mcp"
  else
    sudo -u "${MCP_USER}" "${MCP_VENV}/bin/pip" install -U "${pip_args[@]}" \
      "git+${REPO_URL}.git@${REPO_BRANCH}#subdirectory=mcp"
  fi
}

generate_bearer_token() {
  if [[ -f "${MCP_TOKEN_FILE}" && -s "${MCP_TOKEN_FILE}" ]]; then
    info "Bearer token already exists; reusing."
    return
  fi
  info "Generating bearer token..."
  umask 077
  openssl rand -base64 32 | tr -d '\n' > "${MCP_TOKEN_FILE}"
  chown "${MCP_USER}":"${MCP_USER}" "${MCP_TOKEN_FILE}"
  chmod 600 "${MCP_TOKEN_FILE}"
}

augment_env_file() {
  local token; token="$(cat "${MCP_TOKEN_FILE}")"
  if ! grep -q '^MCP_BEARER_TOKEN=' "${MCP_ENV_FILE}" 2>/dev/null; then
    printf '\nMCP_BEARER_TOKEN=%s\nMCP_HOST=127.0.0.1\nMCP_PORT=%s\nMCP_PATH=/mcp\nAUDIT_LOG_PATH=%s/audit.log\n' \
      "${token}" "${MCP_PORT}" "${MCP_LOG_DIR}" >> "${MCP_ENV_FILE}"
  fi
  chmod 600 "${MCP_ENV_FILE}"
  chown "${MCP_USER}":"${MCP_USER}" "${MCP_ENV_FILE}"
}

install_systemd_unit() {
  info "Installing systemd unit..."
  cp install/pihole-mcp.service "${SYSTEMD_UNIT}"
  systemctl daemon-reload
  systemctl enable --now pihole-mcp.service
}

install_logrotate() {
  if [[ -d /etc/logrotate.d ]]; then
    cp install/logrotate.d/pihole-mcp /etc/logrotate.d/pihole-mcp
  fi
}

install_caddy_repo() {
  if command -v caddy >/dev/null 2>&1; then return; fi
  info "Installing Caddy from official repo..."
  if [[ "${OS_FAMILY}" == "debian" ]]; then
    ensure_pkg debian-keyring debian-archive-keyring apt-transport-https curl gnupg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
      | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
      > /etc/apt/sources.list.d/caddy-stable.list
    apt-get update -qq
    apt_install caddy
  else
    ensure_pkg 'dnf-command(copr)'
    dnf copr enable -y @caddy/caddy
    ensure_pkg caddy
  fi
}

write_caddyfile() {
  info "Writing Caddyfile..."
  if [[ -n "${TLS_HOSTNAME}" ]]; then
    sed "s/\${HOSTNAME}/${TLS_HOSTNAME}/g" install/Caddyfile.tls > /etc/caddy/Caddyfile
  else
    cp install/Caddyfile /etc/caddy/Caddyfile
  fi
  systemctl reload-or-restart caddy
}

install_caddy_full() {
  install_caddy_repo
  write_caddyfile
}

run_tailscale_funnel() {
  if ! command -v tailscale >/dev/null 2>&1; then
    warn "Tailscale not installed; skipping funnel setup."
    return
  fi
  info "Enabling Tailscale Funnel on port 80..."
  tailscale funnel 80 || warn "tailscale funnel exited non-zero — check 'tailscale status'."
}

print_connection_info() {
  local pi_ip; pi_ip="$(hostname -I | awk '{print $1}')"
  local token; token="$(cat "${MCP_TOKEN_FILE}")"
  cat <<EOF

$(color "1;32" "✓ PiHoleMCP installed.")

  Pi-hole Admin:  http://${pi_ip}/admin
  MCP Endpoint:   http://${pi_ip}/mcp
  Bearer Token:   ${token}

Connect from Claude Desktop / Claude.ai:
  Settings → Connectors → Add Custom Connector
  URL:   http://${pi_ip}/mcp
  Auth:  Bearer ${token}

For HTTPS (recommended), see: docs/tls.md
Logs: journalctl -u pihole-mcp -f
Audit log: ${MCP_LOG_DIR}/audit.log
EOF
}

docker_install() {
  info "Running Docker install path..."
  command -v docker >/dev/null 2>&1 || die "Docker not installed. Install Docker first."
  pushd docker >/dev/null
  docker compose up -d
  popd >/dev/null
  info "Docker compose stack started; see docker/docker-compose.yml."
}

main() {
  parse_args "$@"
  require_root
  detect_os

  if [[ ${USE_DOCKER} -eq 1 ]]; then
    docker_install
    exit 0
  fi

  install_pihole
  post_install_pihole
  create_user
  ensure_dirs
  install_python_venv
  generate_bearer_token
  augment_env_file
  install_systemd_unit
  install_logrotate

  if [[ ${INSTALL_CADDY} -eq 1 ]]; then
    install_caddy_full
  else
    warn "Skipping Caddy — wire your own reverse proxy to ${MCP_PREFIX} on :${MCP_PORT}."
  fi

  if [[ ${INSTALL_TS_FUNNEL} -eq 1 ]]; then
    run_tailscale_funnel
  fi

  print_connection_info
}

mkdir -p "${MCP_LOG_DIR}"
main "$@" 2>&1 | tee -a "${MCP_LOG_DIR}/install.log"

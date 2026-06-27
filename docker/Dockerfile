# PiHoleMCP — multi-arch image (linux/arm/v6, linux/arm/v7, linux/arm64, linux/amd64)
FROM python:3.11-slim AS builder

ARG TARGETPLATFORM
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY mcp/pyproject.toml /build/pyproject.toml
COPY mcp/src /build/src

RUN python -m venv /opt/venv \
  && PIP_EXTRA_INDEX_URL="$( [ "${TARGETPLATFORM}" = "linux/arm/v6" ] && echo https://www.piwheels.org/simple )" \
     /opt/venv/bin/pip install --no-cache-dir .

# -------------------------------------------------------------------
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.source="https://github.com/EthanOrr930/PiHoleMCP"
LABEL org.opencontainers.image.title="pihole-mcp"
LABEL org.opencontainers.image.description="Remote MCP server wrapping Pi-hole v6"

RUN groupadd -r pihole-mcp && useradd -r -g pihole-mcp -d /opt/pihole-mcp -s /usr/sbin/nologin pihole-mcp \
  && mkdir -p /var/log/pihole-mcp /etc/pihole-mcp \
  && chown -R pihole-mcp:pihole-mcp /var/log/pihole-mcp /etc/pihole-mcp

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}" \
    PIHOLE_URL="http://127.0.0.1:8081" \
    MCP_HOST="0.0.0.0" \
    MCP_PORT="8473" \
    MCP_PATH="/mcp" \
    AUDIT_LOG_PATH="/var/log/pihole-mcp/audit.log"

USER pihole-mcp
EXPOSE 8473
ENTRYPOINT ["python", "-m", "pihole_mcp"]

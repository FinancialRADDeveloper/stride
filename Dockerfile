FROM python:3.12-slim

# Install uv from the official distroless image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install Litestream for SQLite → S3 replication in production.
# In local docker-compose it is present but never invoked (entrypoint skips
# it when LITESTREAM_REPLICA_URL is not set).
COPY --from=litestream/litestream:0.3.13 /usr/local/bin/litestream /usr/local/bin/litestream

WORKDIR /app

# Install external dependencies first — this layer is cached unless
# pyproject.toml or uv.lock changes, even when source files change.
# --no-install-project skips building the local `stride` package (source
# not present yet); the second sync below installs it once source is copied.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source, then install the local package on top of the
# already-cached dependency layer.
COPY stride/ stride/
RUN uv sync --frozen --no-dev

# Copy entrypoint — handles Litestream restore + replicate when
# LITESTREAM_REPLICA_URL is set; falls through to plain `uv run stride` locally.
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Persistent data volume — SQLite file lives here.
# In production, Litestream replicates this to S3; DATA_DIR is still /data.
ENV DATA_DIR=/data
RUN mkdir -p /data

# Expose the default Dash port
EXPOSE 8050

# App Runner / docker-compose will poll this endpoint to decide if the
# container is healthy before routing traffic to it.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/health')" || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]

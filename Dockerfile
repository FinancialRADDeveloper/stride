FROM python:3.12-slim

# Install uv from the official distroless image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies before copying source so this layer is cached
# unless pyproject.toml or uv.lock changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application source
COPY stride/ stride/

# Persistent data volume — SQLite file lives here.
# Override DATA_DIR to point elsewhere (e.g. an EFS mount) without rebuilding.
ENV DATA_DIR=/data
RUN mkdir -p /data

# Expose the default Dash port
EXPOSE 8050

# App Runner / docker-compose will poll this endpoint to decide if the
# container is healthy before routing traffic to it.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/health')" || exit 1

CMD ["uv", "run", "stride"]

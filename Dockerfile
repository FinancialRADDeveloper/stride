FROM python:3.12-slim

# Install Litestream for SQLite → S3 replication in production
ARG LITESTREAM_VERSION=0.3.13
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL "https://github.com/benbjohnson/litestream/releases/download/v${LITESTREAM_VERSION}/litestream-v${LITESTREAM_VERSION}-linux-amd64.tar.gz" \
       | tar -xz -C /usr/local/bin \
    && apt-get remove -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and pyproject.toml to install stride package
COPY stride/ stride/
COPY pyproject.toml ./

# Install stride package itself without reinstalling dependencies
RUN pip install --no-cache-dir --no-deps .

# Persistent data volume — SQLite file lives here
ENV DATA_DIR=/data
RUN mkdir -p /data

# Entrypoint handles Litestream restore + replicate in production,
# falls back to plain run when LITESTREAM_REPLICA_URL is unset (local dev).
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the default Dash port
EXPOSE 8050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/health')" || exit 1

ENTRYPOINT ["/entrypoint.sh"]

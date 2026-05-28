#!/bin/sh
# docker-entrypoint.sh
#
# In production (App Runner): LITESTREAM_REPLICA_URL is set.
#   - Restores /data/stride.db from S3 on cold start
#   - Runs the app under `litestream replicate` so every WAL frame is
#     streamed to S3 in real-time (near-zero data loss on container crash)
#
# Locally (docker-compose): LITESTREAM_REPLICA_URL is not set.
#   - Falls straight through to `uv run stride` with no overhead.
#
set -e

DATA_DIR=${DATA_DIR:-/data}
mkdir -p "${DATA_DIR}"

if [ -n "${LITESTREAM_REPLICA_URL:-}" ]; then
  echo "[entrypoint] Restoring database from ${LITESTREAM_REPLICA_URL} ..."
  # -if-replica-exists: no-op on first boot (replica doesn't exist yet)
  litestream restore \
    -if-replica-exists \
    -o "${DATA_DIR}/stride.db" \
    "${LITESTREAM_REPLICA_URL}" || true

  echo "[entrypoint] Starting Stride under Litestream replication ..."
  exec litestream replicate \
    -exec "uv run stride" \
    "${DATA_DIR}/stride.db" \
    "${LITESTREAM_REPLICA_URL}"
else
  echo "[entrypoint] No LITESTREAM_REPLICA_URL — running without replication."
  exec uv run stride
fi

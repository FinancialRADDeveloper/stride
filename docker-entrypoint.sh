#!/bin/sh
set -e

if [ -n "${LITESTREAM_REPLICA_URL}" ]; then
  # Restore the database from S3 on cold start (no-op if no replica exists yet).
  litestream restore \
    -if-replica-exists \
    -o "${DATA_DIR}/stride.db" \
    "${LITESTREAM_REPLICA_URL}"

  # Run the app as a subprocess under Litestream replication.
  # Every SQLite WAL frame is streamed to S3 in near real time.
  exec litestream replicate \
    -exec "python -m stride run" \
    "${DATA_DIR}/stride.db" \
    "${LITESTREAM_REPLICA_URL}"
else
  # Local dev — no replication, just run the app.
  exec python -m stride run
fi

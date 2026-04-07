#!/usr/bin/env sh
set -eu

echo "Waiting for Postgres..."
python3 - <<'PY'
import os, socket, time, sys

host = os.environ.get("POSTGRES_HOST", "postgres")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
deadline = time.time() + 60
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print("Postgres is reachable")
            sys.exit(0)
    except OSError:
        time.sleep(1)
print("Timed out waiting for Postgres", file=sys.stderr)
sys.exit(1)
PY

echo "Waiting for Redis..."
python3 - <<'PY'
import os, socket, time, sys

host = os.environ.get("REDIS_HOST", "redis")
port = int(os.environ.get("REDIS_PORT", "6379"))
deadline = time.time() + 60
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print("Redis is reachable")
            sys.exit(0)
    except OSError:
        time.sleep(1)
print("Timed out waiting for Redis", file=sys.stderr)
sys.exit(1)
PY

echo "Waiting for Typesense..."
python3 - <<'PY'
import os, socket, time, sys

host = os.environ.get("TYPESENSE_HOST", "typesense")
port = int(os.environ.get("TYPESENSE_PORT", "8108"))
deadline = time.time() + 60
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print("Typesense is reachable")
            sys.exit(0)
    except OSError:
        time.sleep(1)
print("Timed out waiting for Typesense", file=sys.stderr)
sys.exit(1)
PY

echo "Running migrations..."
alembic upgrade head

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000


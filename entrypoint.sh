#!/bin/bash
set -e

echo "=== LojiNext Backend Starting ==="

echo "Waiting for database..."
until pg_isready -h ${DB_HOST:-db} -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-lojinext_user} -q 2>/dev/null; do
    echo "Database not ready, waiting 2s..."
    sleep 2
done
echo "Database is ready!"

ROLE=${SERVICE_ROLE:-api}

if [ "$ROLE" != "worker" ]; then
  echo "Running database migrations..."
  cd /app
  alembic upgrade head
else
  echo "Worker role detected; skipping Alembic migrations (assumed done by API service)."
fi

echo "Starting uvicorn server..."
if [ "$ROLE" = "worker" ]; then
  # Pass through the command provided by docker-compose (Celery)
  exec "$@"
else
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-1}
fi

#!/bin/bash
set -e

echo "=== LojiNext Backend Starting ==="

# Wait for database to be ready
echo "Waiting for database..."
until pg_isready -h ${DB_HOST:-db} -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-lojinext_user} -q 2>/dev/null; do
    echo "Database not ready, waiting 2s..."
    sleep 2
done
echo "Database is ready!"

# Run Alembic migrations (if alembic directory exists)
if [ -d "/app/alembic" ]; then
    echo "Running database migrations..."
    cd /app
    alembic upgrade head || echo "WARNING: Alembic migrations failed, continuing with create_all fallback..."
fi

# Start the application
echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-1}

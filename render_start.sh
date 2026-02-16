#!/usr/bin/env bash
set -e

echo "=== BuiltPro Render Startup Script ==="
echo "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo ""

# Activate virtual environment if it exists
if [ -f /opt/render/project/.venv/bin/activate ]; then
    echo "Activating virtual environment..."
    source /opt/render/project/.venv/bin/activate
fi

# Check environment
echo "Environment Check:"
echo "  DATABASE_URL: ${DATABASE_URL:+SET}"
echo "  REDIS_URL: ${REDIS_URL:+SET}"
echo "  ENV: ${ENV:-not set}"
echo ""

# Check Redis connection
echo "Checking Redis connection..."
if [ -n "$REDIS_URL" ]; then
    # Extract host from Redis URL
    REDIS_HOST=$(echo "$REDIS_URL" | sed -E 's|redis://([^:/]+).*|\1|')
    if [ -n "$REDIS_HOST" ]; then
        echo "  Redis host: $REDIS_HOST"
        # Try to ping Redis (optional, don't fail if unavailable)
        timeout 5 bash -c "exec 3<>/dev/tcp/$REDIS_HOST/6379" 2>/dev/null && echo "  Redis: Connected" || echo "  Redis: Connection check skipped"
    fi
else
    echo "  Redis: Not configured"
fi
echo ""

# Run database migrations
echo "Running database migrations..."
cd backend
if alembic current >/dev/null 2>&1; then
    echo "  Current revision: $(alembic current 2>/dev/null | grep -oP '^\w+' || echo 'unknown')"
    alembic upgrade head
    if [ $? -eq 0 ]; then
        echo "  Migrations: SUCCESS"
    else
        echo "  Migrations: FAILED (continuing anyway)"
    fi
else
    echo "  Alembic not initialized, skipping migrations"
fi
cd ..
echo ""

# Initialize database if needed
if [ "${INIT_DB_ON_STARTUP:-true}" = "true" ]; then
    echo "Initializing database..."
    python -c "from backend.database import init_db; init_db()" 2>/dev/null && echo "  Database: Initialized" || echo "  Database: Init skipped or failed"
    echo ""
fi

# Start application
echo "=== Starting Application ==="
PORT_VALUE="${PORT:-8000}"
echo "Port: $PORT_VALUE"
echo ""

# Use gunicorn with uvicorn workers for production
if command -v gunicorn &> /dev/null; then
    echo "Starting with Gunicorn..."
    exec gunicorn \
        -k uvicorn.workers.UvicornWorker \
        -w 1 \
        -t 180 \
        --graceful-timeout 180 \
        --log-level "${LOG_LEVEL:-info}" \
        --access-logfile "-" \
        --error-logfile "-" \
        -b "0.0.0.0:$PORT_VALUE" \
        backend.main:app
else
    echo "Starting with Uvicorn..."
    exec uvicorn backend.main:app \
        --host 0.0.0.0 \
        --port "$PORT_VALUE" \
        --log-level "${LOG_LEVEL:-info}"
fi

#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn --host 0.0.0.0 --port 8080 --factory main:init --workers 1 --limit-concurrency 200 --backlog 128 --timeout-keep-alive 5
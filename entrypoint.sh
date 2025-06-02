#!/bin/sh

set -e

echo "Entrypoint: Database (db_match_comments) is reported as healthy. Running migrations for match_comments_service..."

alembic upgrade head

echo "Entrypoint: Migrations finished. Starting application (Uvicorn)..."

exec "$@"
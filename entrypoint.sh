#!/bin/bash
set -e

echo "wait for postgres"
while ! pg_isready -h postgres -U postgres > /dev/null 2>&1; do
    sleep 1
done
echo "postgres is ready"

echo "run alembic migrations"
alembic upgrade head

echo "start app"
exec "$@"

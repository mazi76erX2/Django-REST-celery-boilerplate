#!/bin/bash
set -e

# Wait for database
echo "Waiting for PostgreSQL..."
while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
    sleep 0.5
done
echo "PostgreSQL started"

# Wait for Valkey/Redis
echo "Waiting for Valkey..."
while ! nc -z $CACHE_HOST $CACHE_PORT; do
    sleep 0.5
done
echo "Valkey started"

cd /app/backend

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate --noinput

exec "$@"

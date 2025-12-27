#!/bin/bash
set -e

# Check if database has started
if [ "$DATABASE" = "django-app" ]; then
    echo "Waiting for postgres..."

    while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

until cd /app/backend; do
    echo "Waiting for server volume..."
done

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate --noinput

exec "$@"
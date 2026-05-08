#!/bin/bash
set -e

# Run database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn ecozyhome.wsgi:application --bind 0.0.0.0:8000 --workers 3

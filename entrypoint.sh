#!/bin/sh

# Wait for servers to be up. Otherwise, the app will fail to start.
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
    sleep 0.5
done

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
    sleep 0.5
done

export PYTHONPATH=/app:$PYTHONPATH

case $1 in
    app)
        # Start the service
        gunicorn comicagg.wsgi:application --reload --bind 0.0.0.0:8000 --workers 4 --threads 2
    ;;
    tasks)
        # Start Celery worker
        celery -A comicagg worker -E -l INFO &
        # Start Celery scheduler
        celery -A comicagg beat -l INFO &
        # Start Celery dashboard
        celery -A comicagg flower &
        # Wait for any process to exit
        wait
        # Exit with status of process that exited first
        exit $?
    ;;
  *)
    echo Custom command
    # Search for env vars in the cmd to execute
    # exec "$@"
    exec $(echo "$@" | envsubst)
    ;;
esac

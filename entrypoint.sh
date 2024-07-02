#!/bin/sh

export PYTHONPATH=/app:$PYTHONPATH

case $1 in
    app)
        # Hand over to gunicorn
        exec gunicorn --config /gunicorn.conf.py
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

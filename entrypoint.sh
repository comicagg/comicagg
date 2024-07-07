#!/bin/sh

case $1 in
    app)
        # Hand over to gunicorn
        exec gunicorn --config /gunicorn.conf.py
    ;;
    tasks)
        # Start Celery Beat scheduler
        # Config: https://docs.celeryq.dev/en/stable/reference/cli.html#celery-beat
        celery beat --detach --loglevel $CELERY_LOG_LEVEL
        # Start Celery dashboard
        # Config: https://flower.readthedocs.io/en/latest/config.html
        celery flower &
        # Hand over to the Celery worker
        # Config: https://docs.celeryq.dev/en/stable/reference/cli.html
        exec celery worker --events --loglevel $CELERY_LOG_LEVEL
    ;;
  *)
    echo Custom command
    # Search for env vars in the cmd to execute
    # exec "$@"
    exec $(echo "$@" | envsubst)
    ;;
esac

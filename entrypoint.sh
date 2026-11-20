#!/bin/sh

case $1 in
    migrate)
        # Run database migrations
        exec python src/manage.py migrate
    ;;
    app)
        # Hand over to gunicorn
        exec gunicorn --config /gunicorn.conf.py
    ;;
    tasks)
        # Start Celery dashboard
        # Config: https://flower.readthedocs.io/en/latest/config.html
        celery flower &
        # Hand over to the Celery worker
        # Config: https://docs.celeryq.dev/en/stable/reference/cli.html
        exec celery worker --beat --events --loglevel $CELERY_LOG_LEVEL
    ;;
  *)
    echo Custom command
    # Search for env vars in the cmd to execute
    exec "$@"
    # exec $(echo "$@" | envsubst)
    ;;
esac

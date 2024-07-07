#!/bin/sh

# appdir=$(ls /workspaces | head -n 1 | awk '{print $1}')
# export PYTHONPATH="/workspaces/$appdir/src:$PYTHONPATH"

# Start Celery worker
celery worker --events --loglevel $CELERY_LOG_LEVEL &
# Start Celery scheduler
celery beat --loglevel $CELERY_LOG_LEVEL &
# Start Celery dashboard
celery flower &
# Wait for any process to exit
wait
# Exit with status of process that exited first
exit $?

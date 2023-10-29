#!/bin/sh

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

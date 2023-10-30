# echo "Waiting for PostgreSQL..."
# while ! nc -z $SQL_HOST $SQL_PORT; do
#     sleep 0.1
# done

# Start the service
gunicorn comicagg.wsgi:application --reload --bind 0.0.0.0:8000 --workers 4 --threads 2 &
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

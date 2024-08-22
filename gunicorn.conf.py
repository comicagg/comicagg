# Documentation: https://docs.gunicorn.org/en/stable/settings.html
import multiprocessing

wsgi_app = "comicagg.wsgi:application"
bind = "0.0.0.0:80"

workers = multiprocessing.cpu_count() * 2 + 1
threads = multiprocessing.cpu_count() * 2 + 1

graceful_timeout = 5

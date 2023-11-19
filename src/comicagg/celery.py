import os

from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger("celery_tasks")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "comicagg.settings")

app = Celery("comicagg_tasks")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.autodiscover_tasks(["comicagg"])

import os

from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger("celery_tasks")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "comicagg.settings")

app = Celery("comicagg_tasks")
app.config_from_object("django.conf:settings", namespace="CELERY")
# This will discover tasks in the task module of installed apps
app.autodiscover_tasks()
# This forces discovery in the comicagg module, because it's not an installed app
app.autodiscover_tasks(["comicagg"])

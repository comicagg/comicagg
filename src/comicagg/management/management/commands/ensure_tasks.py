import logging
from collections import namedtuple
from datetime import datetime, timedelta, timezone

from django.core.management.base import BaseCommand, no_translations
from django_celery_beat.models import (
    DAYS,
    HOURS,
    MINUTES,
    IntervalSchedule,
    PeriodicTask,
)

task_logger = logging.getLogger(__name__)

TaskDescription = namedtuple(
    "TaskDescription", ["task", "name", "description", "period", "period_every"]
)

TASKS = [
    TaskDescription(
        task="comicagg.comics.tasks.update_comics.update_comics",
        name="Update comics",
        description="Update all comics",
        period=HOURS,
        period_every=4,
    ),
    TaskDescription(
        task="comicagg.accounts.tasks.inactive_users.inactive_users",
        name="Disable inactive users",
        description="Disable inactive users",
        period=DAYS,
        period_every=1,
    ),
    TaskDescription(
        task="comicagg.tasks.send_pending_emails",
        name="Send emails - 1st try",
        description="Send all pending emails. First try.",
        period=MINUTES,
        period_every=1,
    ),
    TaskDescription(
        task="comicagg.tasks.retry_deferred",
        name="Send emails - Deferred",
        description="Send all pending emails. Retries.",
        period=MINUTES,
        period_every=20,
    ),
]


class Command(BaseCommand):
    help = "Create default tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry",
            action="store_true",
            help="Dry-run",
        )

    @no_translations
    def handle(self, *args, **options):
        for task in TASKS:
            self.ensure_task(task)

    def ensure_task(self, task: TaskDescription):
        period, created = IntervalSchedule.objects.get_or_create(
            every=task.period_every, period=task.period
        )
        if created:
            task_logger.info("Schedule created")
        try:
            PeriodicTask.objects.get(name=task.name, task=task.task)
        except PeriodicTask.DoesNotExist:
            delta = timedelta(days=1)
            tomorrow = datetime.now(timezone.utc) + delta
            PeriodicTask.objects.create(
                name=task.name,
                task=task.task,
                interval=period,
                start_time=datetime(
                    tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=timezone.utc
                ),
                enabled=True,
                description=task.description,
            )
            task_logger.info(f"Task '{task.name}' created")

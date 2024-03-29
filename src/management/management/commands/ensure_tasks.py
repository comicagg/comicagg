import logging
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from typing import cast

from django.core.management.base import BaseCommand, no_translations
from django_celery_beat.models import (
    DAYS,
    HOURS,
    MINUTES,
    IntervalSchedule,
    PeriodicTask,
)

logger = logging.getLogger(__name__)

TaskDescription = namedtuple(
    "TaskDescription", ["task", "name", "description", "period", "period_every"]
)

TASKS = [
    TaskDescription(
        task="comics.tasks.update_comics.update_comics",
        name="Update comics",
        description="Update all comics",
        period=HOURS,
        period_every=4,
    ),
    TaskDescription(
        task="accounts.tasks.inactive_users.inactive_users",
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
        self.dry = options['dry']
        for task in TASKS:
            if self.dry:
                self.dry_task(task)
            else:
                self.ensure_task(task)

    def ensure_task(self, task: TaskDescription):
        period, created = IntervalSchedule.objects.get_or_create(
            every=task.period_every, period=task.period
        )
        if created:
            logger.info("Schedule created")

        if old_tasks := PeriodicTask.objects.filter(name=task.name):
            # Update the task
            old_task = old_tasks[0]
            old_task.task = task.task
            old_task.interval = period
            old_task.enabled = True
            old_task.description = task.description
            old_task.save()
            logger.info(f"Task '{task.name}' updated")
        else:
            # Create the task
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
            logger.info(f"Task '{task.name}' created")

    def dry_task(self, task: TaskDescription):
        old_period = IntervalSchedule.objects.filter(every=task.period_every, period=task.period).count()
        if not old_period:
            print(f'Period every {task.period_every} {task.period} would be CREATED')

        if old_task := PeriodicTask.objects.filter(name=task.name):
            print(f'Task {task.name} would be UPDATED')
        else:
            print(f'Task {task.name} would be CREATED')

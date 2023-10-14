from datetime import datetime, timedelta, timezone

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User

from comicagg.accounts.utils import get_profile

task_logger = get_task_logger(__name__)


@shared_task
def inactive_users(dry_run=False):
    """Mark users as inactive if they haven't logged in in a while.

    The threshold is settings.INACTIVE_DAYS
    """
    if dry_run:
        task_logger.info("Dry-run")
        print("Dry-run")
    users = User.objects.filter(is_active__exact=1)
    limit = datetime.now(timezone.utc) - timedelta(settings.INACTIVE_DAYS)

    for user in users:
        user_profile = get_profile(user)
        if user_profile.last_read_access < limit:
            if dry_run:
                d = datetime.now(timezone.utc) - user_profile.last_read_access
                task_logger.info(f"User {user.username:>20} {d.days} days inactive")
            else:
                task_logger.info(f"Setting user {user} as inactive")
                user.is_active = False
                user.save()
                user.unreadcomic_set.all().delete()
    task_logger.info("Execution summary")
    task_logger.info(f"{len(users)} total users")
    
    inactive_count = User.objects.filter(is_active__exact=0).count()
    task_logger.info(f"{inactive_count} inactive users")

    return "Ok"

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User

task_logger = get_task_logger(__name__)


@shared_task
def max_unreads_per_user():
    """Limit the maximum number of unread comics a user can have."""
    users = User.objects.all()
    for user in users:
        user_subscriptions = user.subscription_set.all()
        for subscription in user_subscriptions:
            unreads = user.unreadstrip_set.filter(
                comic__exact=subscription.comic
            ).order_by("-id")
            if unreads.count() > settings.MAX_UNREADS_PER_USER:
                task_logger.info(f"{user} {subscription.comic} {unreads.count()}")
                sid = unreads[20].id
                deletes = (
                    user.unreadstrip_set.filter(comic__exact=subscription.comic)
                    .order_by("-id")
                    .filter(id__lte=sid)
                )
                deletes.delete()

        return "Ok"

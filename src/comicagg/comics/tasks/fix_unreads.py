from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth.models import User

from comicagg.comics.models import Subscription, UnreadStrip

task_logger = get_task_logger(__name__)


@shared_task
def fix_unread_comics():
    """Deletes unread comics for comics that the user is not subscribed to."""
    all_users = User.objects.all()

    for user in all_users:
        task_logger.info(f"User: {user}")
        subs: list[Subscription] = user.subscription_set.all().select_related("comic")
        comics = [sub.comic.id for sub in subs]
        unreads = UnreadStrip.objects.filter(user__exact=user).exclude(comic__in=comics)
        unreads.delete()

    return "Ok"

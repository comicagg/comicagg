from celery import shared_task
from celery.utils.log import get_task_logger
from mailer.engine import send_all
from mailer.models import Message

task_logger = get_task_logger(__name__)


@shared_task
def send_pending_emails():
    send_all()
    return True

@shared_task
def retry_deferred():
    Message.objects.retry_deferred()
    return True

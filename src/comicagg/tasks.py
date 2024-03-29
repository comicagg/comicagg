from typing import cast
from celery import shared_task
from celery.utils.log import get_task_logger
from mailer.engine import send_all
from mailer.models import Message, MessageManager

task_logger = get_task_logger(__name__)


@shared_task
def send_pending_emails():
    send_all()
    return True

@shared_task
def retry_deferred():
    cast(MessageManager, Message.objects).retry_deferred()
    return True

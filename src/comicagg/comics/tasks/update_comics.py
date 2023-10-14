import sys
from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.mail import mail_managers
from comicagg.comics.update import update_comic, NoMatchException
from comicagg.comics.models import Comic

task_logger = get_task_logger(__name__)


@shared_task
def update_comics():
    """Updates comics looking for a new comic strip."""

    comic_ids: list[int] = list(Comic.objects.values_list("id", flat=True))
    for comic_id in comic_ids:
        update_comic_task.delay(comic_id)
    return "Ok"


@shared_task
def update_comic_task(comic_id: int) -> bool:
    comic = Comic.objects.get(pk=comic_id)
    updated = False
    error = False
    try:
        updated = update_comic(comic)
    except NoMatchException:
        comic.last_update_status = "No match during update"
        error = True
    except:
        comic.last_update_status = f"Error: {sys.exc_info()[1]}"
        error = True
    finally:
        if error:
            comic.save()

    return {"updated": updated, "status": comic.last_update_status if error else ""}

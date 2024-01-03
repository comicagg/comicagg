import sys

from celery import shared_task
from celery.utils.log import get_task_logger
from comicagg.comics.models import Comic
from comicagg.comics.update import NoMatchException, update_comic

task_logger = get_task_logger(__name__)


@shared_task
def update_comics():
    """Updates comics looking for a new comic strip."""

    comic_ids: list[int] = list(Comic.objects.values_list("id", flat=True))
    for comic_id in comic_ids:
        update_comic_task.apply_async(
            (comic_id,), periodic_task_name=f"Update comic {comic_id}"
        )
    return "Ok"


@shared_task
def update_comic_task(comic_id: int) -> dict[str, bool | str]:
    comic = Comic.objects.get(pk=comic_id)
    updated = False
    error = False
    try:
        updated = update_comic(comic)
        comic.last_update_status = "Success"
    except NoMatchException:
        comic.last_update_status = "No match during update"
    except Exception:
        comic.last_update_status = f"Error: {sys.exc_info()[1]}"
    finally:
        comic.save()

    return {"updated": updated, "status": comic.last_update_status if error else ""}

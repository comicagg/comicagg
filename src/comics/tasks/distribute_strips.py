from celery import shared_task
from django.db import transaction

from ..models import Comic, Strip, Subscription, UnreadStrip

BATCH_SIZE = 1000


@shared_task
def distribute_pending_strips() -> int:
    """Queue one distribution task per comic with pending strips."""
    comic_ids = (
        Strip.objects.filter(unreads_distributed=False)
        .order_by()
        .values_list("comic_id", flat=True)
        .distinct()
    )
    queued = 0
    for comic_id in comic_ids.iterator(chunk_size=BATCH_SIZE):
        distribute_comic_strips.delay(comic_id)
        queued += 1
    return queued


@shared_task
def distribute_comic_strips(comic_id: int) -> dict[str, int]:
    """Distribute a comic's pending strips atomically in bounded batches."""
    with transaction.atomic():
        # Serialize tasks for a comic before taking the pending-strip snapshot.
        Comic.objects.select_for_update().get(pk=comic_id)
        strip_ids = list(
            Strip.objects.select_for_update()
            .filter(comic_id=comic_id, unreads_distributed=False)
            .order_by("pk")
            .values_list("pk", flat=True)
        )
        batch: list[UnreadStrip] = []
        created = 0
        for strip_id in strip_ids:
            existing_users = UnreadStrip.objects.filter(strip_id=strip_id).values_list(
                "user_id", flat=True
            )
            subscriber_ids = (
                Subscription.objects.filter(comic_id=comic_id, user__is_active=True)
                .exclude(user_id__in=existing_users)
                .order_by()
                .values_list("user_id", flat=True)
                .distinct()
            )
            for user_id in subscriber_ids.iterator(chunk_size=BATCH_SIZE):
                batch.append(
                    UnreadStrip(user_id=user_id, strip_id=strip_id, comic_id=comic_id)
                )
                if len(batch) == BATCH_SIZE:
                    UnreadStrip.objects.bulk_create(batch, batch_size=BATCH_SIZE)
                    created += len(batch)
                    batch = []
        if batch:
            UnreadStrip.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            created += len(batch)
        Strip.objects.filter(pk__in=strip_ids).update(unreads_distributed=True)
    return {"strips": len(strip_ids), "unreads": created}

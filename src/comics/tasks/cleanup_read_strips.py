from celery import shared_task
from django.db import models, transaction

from ..models import Subscription, UnreadStrip


@shared_task
def cleanup_read_strips(batch_size: int = 1000, max_batches: int = 100) -> int:
    """Reclaim logically read rows in bounded, independently committed batches."""
    if batch_size < 1 or max_batches < 1:
        raise ValueError("Cleanup limits must be positive.")
    subscription = Subscription.objects.filter(
        user_id=models.OuterRef("user_id"),
        comic_id=models.OuterRef("comic_id"),
        read_through__gte=models.OuterRef("read_sequence"),
    )
    # Pending distribution still uses these rows to suppress duplicate delivery.
    read_rows = UnreadStrip.objects.filter(
        models.Exists(subscription), strip__unreads_distributed=True
    )
    deleted = 0
    for _ in range(max_batches):
        with transaction.atomic():
            ids = list(
                read_rows.order_by("pk").values_list("pk", flat=True)[:batch_size]
            )
            if not ids:
                break
            # Recheck the predicate in case a maintenance operation changed a row.
            count, _ = read_rows.filter(pk__in=ids).delete()
            deleted += count
    return deleted

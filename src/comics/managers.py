from django.db import models, transaction

from .fields import ComicStatus

VISIBLE_STATUS = [ComicStatus.ACTIVE, ComicStatus.ENDED, ComicStatus.BROKEN]


class ComicManager(models.Manager):
    def available(self):
        """Return only comics that should be visible to the users."""
        # TODO: test
        query = models.Q(status__in=VISIBLE_STATUS)
        return self.filter(query)


class SubscriptionQuerySet(models.QuerySet):
    def delete(self):
        from .models import Comic, UnreadStrip

        with transaction.atomic(using=self.db):
            comic_ids = self.order_by().values_list("comic_id", flat=True).distinct()
            list(
                Comic.objects.using(self.db)
                .filter(pk__in=comic_ids)
                .order_by("pk")
                .select_for_update()
            )
            matching = self.filter(
                user_id=models.OuterRef("user_id"),
                comic_id=models.OuterRef("comic_id"),
            )
            UnreadStrip.objects.using(self.db).filter(models.Exists(matching)).delete()
            return super().delete()


class SubscriptionManager(models.Manager.from_queryset(SubscriptionQuerySet)):
    def available(self):
        """Return only comics that should be visible to the users."""
        # TODO: test
        query = models.Q(comic__status__in=VISIBLE_STATUS)
        return self.filter(query).select_related("comic")


class UnreadStripManager(models.Manager):
    def active(self):
        from .models import Subscription

        subscription = Subscription.objects.filter(
            user_id=models.OuterRef("user_id"),
            comic_id=models.OuterRef("comic_id"),
            read_through__lt=models.OuterRef("read_sequence"),
        )
        return self.filter(models.Exists(subscription))

    def available(self):
        """Return only unread strips of comics that should be visible to the users."""
        # TODO: test
        query = models.Q(strip__comic__status__in=VISIBLE_STATUS)
        return self.active().filter(query)

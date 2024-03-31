from django.db import models

from .fields import ComicStatus

VISIBLE_STATUS = [ComicStatus.ACTIVE, ComicStatus.ENDED, ComicStatus.BROKEN]


class ComicManager(models.Manager):
    def available(self):
        """Return only comics that should be visible to the users."""
        # TODO: test
        query = models.Q(status__in=VISIBLE_STATUS)
        return self.filter(query)


class SubscriptionManager(models.Manager):
    def available(self):
        """Return only comics that should be visible to the users."""
        # TODO: test
        query = models.Q(comic__status__in=VISIBLE_STATUS)
        return self.filter(query).select_related("comic")


class UnreadStripManager(models.Manager):
    def available(self):
        """Return only unread strips of comics that should be visible to the users."""
        # TODO: test
        query = models.Q(strip__comic__status__in=VISIBLE_STATUS)
        return self.filter(query)

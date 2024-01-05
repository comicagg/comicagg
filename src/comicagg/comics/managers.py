from django.db import models
from django.db.models import Q

from comicagg.comics.fields import ComicStatus

VISIBLE_STATUS = [ComicStatus.ACTIVE, ComicStatus.ENDED, ComicStatus.BROKEN]


class ComicManager(models.Manager):
    def available(self):
        """Return only comics that should be visible to the users."""
        # TODO: test
        query = Q(status__in=VISIBLE_STATUS)
        return self.filter(query)


class SubscriptionManager(models.Manager):
    def available(self):
        """Return only comics that should be visible to the users."""
        # TODO: test
        query = Q(comic__status__in=VISIBLE_STATUS)
        return self.filter(query).select_related("comic")


class UnreadStripManager(models.Manager):
    def available(self):
        """Return only unread strips of comics that should be visible to the users."""
        # TODO: test
        query = Q(strip__comic__status__in=VISIBLE_STATUS)
        return self.filter(query)

from django.db import models
from django.db.models import Q


class ComicManager(models.Manager):
    def available(self, include_ended=True):
        """Return only comics that should be visible to the users.
        Ended comics are included by default, but can be excluded if neccessary."""
        # TODO: test
        query = Q(active=True) & Q(ended=False)
        if include_ended:
            query = Q(active=True) | (Q(active=True) & Q(ended=True))
        return self.filter(query)


class SubscriptionManager(models.Manager):
    def available(self, include_ended=True):
        """Return only comics that should be visible to the users,
        including ended comic by default."""
        # TODO: test
        query = Q(comic__active=True) & Q(comic__ended=False)
        if include_ended:
            query = Q(comic__active=True) | (
                Q(comic__active=True) & Q(comic__ended=True)
            )
        return self.filter(query).select_related("comic")


class UnreadStripManager(models.Manager):
    def available(self, include_ended=True):
        """Return only unread strips of comics that should be visible to the users."""
        # TODO: test
        query = Q(strip__comic__active=True)
        if include_ended:
            query = Q(strip__comic__active=True) | (
                Q(strip__comic__active=True) & Q(strip__comic__ended=True)
            )
        return self.filter(query)

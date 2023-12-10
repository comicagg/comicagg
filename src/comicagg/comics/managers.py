from django.db import models
from django.db.models import Q


class ComicManager(models.Manager):
    def available(self, include_ended=True):
        """Return only comics that should be visible to the users.
        Ended comics are included by default, but can be excluded if neccessary."""
        return self.exclude(Q(active=False) | Q(ended=include_ended))


class SubscriptionManager(models.Manager):
    def available(self, include_ended=True):
        """Return only comics that should be visible to the users.
        Ended comics are included by default, but can be excluded if neccessary."""
        return self.exclude(Q(comic__active=False) | Q(comic__ended=include_ended))


class UnreadStripManager(models.Manager):
    def available(self, include_ended=True):
        """Return only unread strips of comics that should be visible to the users."""
        return self.exclude(
            Q(strip__comic__active=False) | Q(strip__comic__ended=include_ended)
        )

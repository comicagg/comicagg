import logging
from typing import Any

from django.contrib.auth import models as auth_models
from django.db import models
from django.db.models import Max, Count
from django.utils.translation import gettext_lazy as _

from comicagg.comics.managers import SubscriptionManager, UnreadStripManager

from comicagg.comics.models import Comic, Strip, UnreadComic

logger = logging.getLogger(__name__)


class User(auth_models.User):
    """Proxy class of the default's User class.
    Adds helper class methods."""

    unreadcomic_set: UnreadStripManager
    subscription_set: SubscriptionManager
    request_set: Any
    newblog_set: Any
    newcomic_set: Any

    class Meta:
        proxy = True

    # #####################
    # #   Subscriptions   #
    # #####################
    def subscriptions(self):
        """Returns all subscribed comics, including ended."""
        return self.subscription_set.available()

    def subscriptions_active(self):
        """Returns all subscribed comics, excluding ended."""
        return self.subscription_set.available(include_ended=False)

    def comics_subscribed(self):
        """Return the ordered list of comics that the user is subscribed."""
        comic_ids = [subscription.comic.id for subscription in self.subscriptions()]
        return (
            Comic.objects.available()
            .prefetch_related("subscription_set")
            .prefetch_related("strip_set")
            .filter(id__in=comic_ids)
        )

    def is_subscribed(self, comic: Comic):
        """Check if the user is subscribed to a comic."""
        return self.subscriptions().filter(comic__id=comic.id).count() == 1

    def subscribe(self, comic: Comic):
        """Subscribe the user to this comic, adding it last to his list."""
        if self.is_subscribed(comic):
            return
        if not comic.active or comic.ended:
            raise Exception("Cannot subscribe to an ended or inactive comic")
        # Calculate the position for the comic, it'll be the last
        # max_position can be None if there are no comics
        max_position = self.subscriptions().aggregate(pos=Max("position"))["pos"] or 0
        next_pos = max_position + 1
        self.subscription_set.create(comic=comic, position=next_pos)
        if last_strip := Strip.objects.filter(comic=comic).last():
            UnreadComic.objects.create(user=self, comic=comic, strip=last_strip)

    # #####################
    # #   Unread strips   #
    # #####################
    def unread_strips(self):
        """Return unread strips for all subscribed comics, including ended."""
        return self.unreadcomic_set.available()

    def unread_strips_for(self, comic: Comic):
        """Return available unread strips for a comic."""
        return self.unreadcomic_set.available().filter(comic=comic, user=self)

    def comics_unread(self) -> list[Comic]:
        """Return a list of comics (possibly ended) that have unread strips
        ordered by subscription position."""
        unreads = self.unread_strips().select_related("comic")
        unread_comic_ids = list({unread.comic.id for unread in unreads})
        return [
            subscription.comic
            for subscription in self.subscriptions()
            if subscription.comic.id in unread_comic_ids
        ]

    def comics_unread_count(self) -> int:
        """Return the number of comics with unread strips."""
        return self.unread_strips().aggregate(Count("comic", distinct=True))[
            "comic__count"
        ]

    # ##################
    # #   New comics   #
    # ##################

    def comics_new(self) -> list[Comic]:
        """Return the list of comics that are new for this user, including ended ones."""
        new_comics = self.newcomic_set.select_related("comic")
        new_comics_ids = [newcomic.comic.id for newcomic in new_comics]
        return (
            Comic.objects.available()
            .prefetch_related("subscription_set")
            .filter(pk__in=new_comics_ids)
        )


class UserProfile(models.Model):
    user = models.OneToOneField(
        auth_models.User, related_name="user_profile", on_delete=models.CASCADE
    )

    last_read_access = models.DateTimeField()

    class Meta:
        ordering = ["user"]
        verbose_name = _("User profile")
        verbose_name_plural = _("User profiles")

    def __str__(self):
        return str(self.user)

    def is_active(self):
        return bool(self.user.is_active)

    is_active.boolean = True

import logging
from typing import Any

from django.contrib.auth import models as auth_models
from django.db import models
from django.db.models import Count, Max
from django.utils.translation import gettext_lazy as _

from comicagg.comics.fields import ComicStatus
from comicagg.comics.managers import SubscriptionManager, UnreadStripManager
from comicagg.comics.models import Comic, Strip, UnreadStrip

logger = logging.getLogger(__name__)


class InvalidComicError(Exception):
    """Exception raised when trying to subscribe to an invalid comic."""

    pass


class IncompleteListError(Exception):
    """Exception raised when a list of comics is incomplete."""

    pass


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


class User(auth_models.User):
    """Proxy class of the default's User class.
    Adds helper class methods."""

    unreadstrip_set: UnreadStripManager
    subscription_set: SubscriptionManager
    request_set: Any
    newblog_set: Any
    newcomic_set: Any

    user_profile: UserProfile

    class Meta:
        proxy = True

    # #####################
    # #   Subscriptions   #
    # #####################
    def subscriptions(self) -> SubscriptionManager:
        """Returns all subscribed comics, including ended."""
        return self.subscription_set.available()

    def subscription_count(self) -> int:
        """Returns all subscribed comics, including ended."""
        return self.subscription_set.available().count()

    def comics_subscribed(self) -> list[Comic]:
        """Return the ordered list of comics that the user is subscribed."""
        comic_ids = [subscription.comic.id for subscription in self.subscriptions()]
        return list(
            Comic.objects.available()
            .prefetch_related("subscription_set")
            .prefetch_related("strip_set")
            .filter(id__in=comic_ids)
        )

    def is_subscribed(self, comic: Comic) -> bool:
        """Check if the user is subscribed to a comic."""
        return self.subscriptions().filter(comic__id=comic.id).count() == 1

    def subscribe(self, comic: Comic) -> None:
        """Subscribe the user to this comic, adding it last to his list."""
        if self.is_subscribed(comic):
            return
        if comic.status in [ComicStatus.INACTIVE]:
            raise InvalidComicError("Cannot subscribe to this comic")
        # Calculate the position for the comic, it'll be the last
        # max_position can be None if there are no comics
        max_position = self.subscriptions().aggregate(pos=Max("position"))["pos"] or 0
        next_pos = max_position + 1
        self.subscription_set.create(comic=comic, position=next_pos)
        if last_strip := Strip.objects.filter(comic=comic).last():
            UnreadStrip.objects.create(user=self, comic=comic, strip=last_strip)
        # FUTURE: return next_pos so that the following subscription can be used with a known position?

    def subscribe_list(self, comic_id_list: list[int]) -> None:
        """Add the comics from the list. Ignores comics that are already subscribed,
        ended or inactive."""
        comics = Comic.objects.available().in_bulk(comic_id_list)
        for comic in comics.values():
            self.subscribe(comic)

    def unsubscribe(self, comic: Comic) -> None:
        """Remove the comic from the list of subscriptions."""
        self.unreadstrip_set.filter(comic=comic).delete()
        self.subscription_set.filter(comic=comic).delete()
        self.subscriptions_recalculate_positions()

    def unsubscribe_list(self, comic_id_list: list[int]) -> None:
        """Remove the comic from the list of subscriptions."""
        self.unreadstrip_set.filter(comic__id__in=comic_id_list).delete()
        self.subscription_set.filter(comic__id__in=comic_id_list).delete()
        self.subscriptions_recalculate_positions()

    def unsubscribe_all(self) -> None:
        """Remove all of the user's subscriptions."""
        self.unreadstrip_set.all().delete()
        self.subscription_set.all().delete()

    def subscriptions_reorder(self, comic_id_list: list[int]) -> None:
        """Reorder the subscriptions according to the list of comic ids."""
        # TODO: test
        # TODO: implement
        clean_id_list = set(comic_id_list)
        subscriptions = self.subscription_set.all()
        if subscriptions.count() != len(clean_id_list):
            raise IncompleteListError(
                "The list of comics is incomplete or contains invalid comics"
            )

        for subscription in subscriptions:
            subscription.position = comic_id_list.index(subscription.comic.id) + 1
            subscription.save()

    def subscriptions_recalculate_positions(self) -> None:
        """Recalculate the position of each subscription."""
        subscriptions = self.subscription_set.all()
        for i, subscription in enumerate(subscriptions):
            subscription.position = i
            subscription.save()

    # #####################
    # #   Unread strips   #
    # #####################
    def unread_strips(self) -> UnreadStripManager:
        """Return unread strips for all subscribed comics, including ended."""
        return self.unreadstrip_set.available()

    def unread_strips_for(self, comic: Comic) -> UnreadStripManager:
        """Return available unread strips for a comic."""
        return self.unreadstrip_set.available().filter(comic=comic, user=self)

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

    def mark_unread(self, comic: Comic) -> bool:
        """Sets a comic as unread adding the last strip as unread for this user."""
        if not self.is_subscribed(comic):
            return False
        if self.unread_strips_for(comic).count():
            return False
        if strip := comic.last_strip:
            self.unreadstrip_set.create(user=self, comic=comic, strip=strip)
        return True

    def mark_read(self, comic: Comic, vote=0) -> None:
        """Mark the comic as read, removing the unread strips and updating the votes."""
        if not self.is_subscribed(comic):
            return
        votes = 0
        value = 0
        if vote < 0:
            votes = 1
            value = 0
        elif vote > 0:
            votes = 1
            value = 1
        comic.total_votes += votes
        comic.positive_votes += value
        comic.save()
        self.unreadstrip_set.filter(comic=comic).delete()

    def mark_read_all(self) -> None:
        """Mark all comics as read."""
        self.unreadstrip_set.all().delete()

    # ##################
    # #   New comics   #
    # ##################

    def comics_new(self) -> list[Comic]:
        """Return the list of comics that are new for this user."""
        new_comics = self.newcomic_set.select_related("comic")
        new_comics_ids = [newcomic.comic.id for newcomic in new_comics]
        return list(
            Comic.objects.available()
            .prefetch_related("subscription_set")
            .filter(pk__in=new_comics_ids)
        )

    def comics_new_count(self) -> int:
        """Return the number of new comics for this user."""
        return self.newcomic_set.count()

    def comics_new_forget(self, comic: Comic) -> None:
        """Forget all new comics for this user."""
        # TODO: test
        self.newcomic_set.filter(comic=comic).delete()

    def comics_new_forget_all(self) -> None:
        """Forget all new comics for this user."""
        # TODO: test
        self.newcomic_set.all().delete()

    def comic_is_new(self, comic: Comic) -> bool:
        """Check if a comic is new for this user."""
        return self.newcomic_set.filter(comic=comic).count() == 1

    # #################
    # #   New blogs   #
    # #################

    def blogs_new_count(self):
        """Return the list of new blogs for this user."""
        return self.newblog_set.count()

    # ################
    # #   Requests   #
    # ################

    def requests_accepted_count(self) -> int:
        """Return the count of accepted requests for this user."""
        return self.request_set.filter(done__exact=1).filter(rejected__exact=0)

    def requests_rejected_count(self) -> int:
        """Return the count of rejected requests for this user."""
        return self.request_set.filter(rejected__exact=1)

    def requests_pending_count(self) -> int:
        """Return the count of pending requests for this user."""
        return self.request_set.filter(done__exact=0).filter(rejected__exact=0)

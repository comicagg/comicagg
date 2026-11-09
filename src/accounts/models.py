import logging
from typing import Any

from django.contrib.auth import models as auth_models
from django.db import models, transaction
from django.db.models import Case, Count, F, Max, Value, When
from django.db.models.functions import Greatest
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from comics.fields import ComicStatus
from comics.managers import SubscriptionManager, UnreadStripManager
from comics.models import Comic, Strip, Subscription, UnreadStrip

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
    @cached_property
    def subscriptions(self) -> SubscriptionManager:
        """Returns all subscribed comics, including ended."""
        return self.subscription_set.available()

    @cached_property
    def subscription_count(self) -> int:
        """Returns all subscribed comics, including ended."""
        return self.subscriptions.count()

    @cached_property
    def comics_subscribed(self) -> list[Comic]:
        """Return the ordered list of comics that the user is subscribed."""
        return [subscription.comic for subscription in self.subscriptions]

    def is_subscribed(self, comic: Comic) -> bool:
        """Check if the user is subscribed to a comic."""
        return self.subscriptions.filter(comic__id=comic.id).exists()

    def subscribe(self, comic: Comic) -> None:
        """Subscribe the user to this comic, adding it last to his list."""
        if self.is_subscribed(comic):
            return
        if comic.status in [ComicStatus.INACTIVE]:
            raise InvalidComicError("Cannot subscribe to this comic")
        # Calculate the position for the comic, it'll be the last
        # max_position can be None if there are no comics
        max_position = self.subscriptions.aggregate(pos=Max("position"))["pos"] or 0
        next_pos = max_position + 1
        self.subscription_set.get_or_create(
            comic=comic, defaults={"position": next_pos}
        )
        # FUTURE: return next_pos so that the following subscription can be used with a known position?
        self.comics_new_forget(comic)
        self._invalidate_comic_cache()

    def subscribe_list(self, comic_id_list: list[int]) -> None:
        """Add the comics from the list. Ignores comics that are already subscribed,
        ended or inactive."""
        comics = Comic.objects.available().in_bulk(comic_id_list)
        for comic_id in comic_id_list:
            comic = comics.get(comic_id)
            if comic is not None:
                self.subscribe(comic)

    def unsubscribe(self, comic: Comic) -> None:
        """Remove the comic from the list of subscriptions."""
        self.unsubscribe_list([comic.pk])

    def unsubscribe_list(self, comic_id_list: list[int]) -> None:
        """Remove the comic from the list of subscriptions."""
        with transaction.atomic():
            list(
                Comic.objects.filter(pk__in=comic_id_list)
                .order_by("pk")
                .select_for_update()
            )
            list(
                self.subscription_set.order_by("pk")
                .select_for_update()
                .values_list("pk", flat=True)
            )
            self.unreadstrip_set.filter(comic_id__in=comic_id_list).delete()
            self.subscription_set.filter(comic_id__in=comic_id_list).delete()
            self.subscriptions_recalculate_positions()
        self._invalidate_comic_cache()

    def unsubscribe_all(self) -> None:
        """Remove all of the user's subscriptions."""
        self.unsubscribe_list(
            list(self.subscription_set.values_list("comic_id", flat=True))
        )

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
            subscription.save(update_fields=["position"])

    def subscriptions_recalculate_positions(self) -> None:
        """Recalculate the position of each subscription."""
        subscriptions = self.subscription_set.all()
        for i, subscription in enumerate(subscriptions):
            subscription.position = i
            subscription.save(update_fields=["position"])

    def _invalidate_comic_cache(self) -> None:
        for name in (
            "subscriptions",
            "subscription_count",
            "comics_subscribed",
            "unread_strips",
            "comics_unread_count",
            "comics_new_count",
        ):
            self.__dict__.pop(name, None)

    # #####################
    # #   Unread strips   #
    # #####################
    @cached_property
    def unread_strips(self) -> UnreadStripManager:
        """Return unread strips for all subscribed comics, including ended."""
        return self.unreadstrip_set.available()

    def unread_strips_for(self, comic: Comic) -> UnreadStripManager:
        """Return available unread strips for a comic."""
        return self.unreadstrip_set.available().filter(comic=comic, user=self)

    def comics_unread(self) -> list[Comic]:
        """Return a list of comics (possibly ended) that have unread strips
        ordered by subscription position."""
        unreads = self.unread_strips.select_related("comic")
        unread_comic_ids = list({unread.comic.id for unread in unreads})
        return [
            subscription.comic
            for subscription in self.subscriptions
            if subscription.comic.id in unread_comic_ids
        ]

    @cached_property
    def comics_unread_count(self) -> int:
        """Return the number of comics with unread strips."""
        return self.unread_strips.aggregate(Count("comic", distinct=True))[
            "comic__count"
        ]

    def mark_unread(self, comic: Comic) -> bool:
        """Sets a comic as unread adding the last strip as unread for this user."""
        with transaction.atomic():
            Comic.objects.select_for_update().get(pk=comic.pk)
            subscription = (
                self.subscriptions.select_for_update().filter(comic=comic).first()
            )
            if subscription is None:
                return False
            strip = Strip.objects.filter(comic=comic).first()
            if strip is None:
                return True
            existing = self.unreadstrip_set.filter(strip=strip).first()
            if (
                existing is not None
                and existing.read_sequence > subscription.read_through
            ):
                return False
            if existing is not None:
                existing.delete()
            self.unreadstrip_set.create(comic=comic, strip=strip)
        self._invalidate_comic_cache()
        return True

    def mark_read(self, comic: Comic, vote=0, *, snapshot: str) -> None:
        """Mark the displayed prefix as read and optionally vote."""
        from comics.read_state import load_snapshot

        boundaries = [
            row for row in load_snapshot(snapshot, self.pk) if row[1] == comic.pk
        ]
        with transaction.atomic():
            if vote:
                Comic.objects.select_for_update().get(pk=comic.pk)
            if not self._advance_read_markers(boundaries):
                return
            if vote:
                Comic.objects.filter(pk=comic.pk).update(
                    total_votes=F("total_votes") + 1,
                    positive_votes=F("positive_votes") + int(vote > 0),
                )
        self._invalidate_comic_cache()

    def mark_read_all(self, *, snapshot: str) -> None:
        """Mark only the prefixes included in the reader snapshot as read."""
        from comics.read_state import load_snapshot

        with transaction.atomic():
            self._advance_read_markers(load_snapshot(snapshot, self.pk))
        self._invalidate_comic_cache()

    def _advance_read_markers(self, boundaries: list[list[int]]) -> int:
        if not boundaries:
            return 0
        subscriptions = Subscription.objects.filter(
            user=self,
            pk__in=[row[0] for row in boundaries],
            comic__status__in=[
                ComicStatus.ACTIVE,
                ComicStatus.ENDED,
                ComicStatus.BROKEN,
            ],
        )
        # Lock subscription rows in a stable order across overlapping snapshots.
        ids = list(
            subscriptions.order_by("pk")
            .select_for_update(of=("self",))
            .values_list("pk", flat=True)
        )
        if not ids:
            return 0
        return Subscription.objects.filter(pk__in=ids).update(
            read_through=Greatest(
                F("read_through"),
                Case(
                    *[
                        When(
                            pk=subscription_id, comic_id=comic_id, then=Value(boundary)
                        )
                        for subscription_id, comic_id, boundary in boundaries
                    ],
                    default=F("read_through"),
                    output_field=models.PositiveBigIntegerField(),
                ),
            )
        )

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

    @cached_property
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

    # TODO Rename this to post
    @cached_property
    def blogs_new_count(self):
        """Return the list of new blogs for this user."""
        return self.newblog_set.count()

    def posts_forget_all(self) -> None:
        """Forget all new posts for this user."""
        # TODO: test
        self.newblog_set.all().delete()

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

# -*- coding: utf-8 -*-
import logging
import random
from django.db.models import Max
from comicagg.comics.models import Comic, ComicHistory, UnreadComic, NewComic, active_comics

logger = logging.getLogger(__name__)

class UserOperations(object):
    """This class allows operations with comic stuff and a certain user.

    All operations related to comics and users should be done with this class and not directly with the ORM.
    """

    def __init__(self, user, **kwargs):
        super().__init__(**kwargs)
        self.user = user

    # Unread comics
    def unread_comic_set(self):
        """Return the filtered UnreadComic QuerySet for the user."""
        return self.user.unreadcomic_set.exclude(comic__active=False, comic__ended=False)

    def unread_comics(self):
        """Get a list of comics that have unread strips ordered by the position chosen by the user.
        
        Does not include the strips for each comic.
        """
        unreads = self.unread_comic_set()
        # Build a list of comic ids to later get the comics correctly ordered from all_comics
        comic_ids = list(set([unread.comic.id for unread in unreads]))
        return [comic for comic in self.subscribed_comics() if comic.id in comic_ids]

    def unread_comics_count(self):
        """Get a list of tuples of comics with unread strips ordered by the position chosen by the user.

        First value is the comic, second is the number of unread strips.
        """
        # NOTE: this is exactly the same as unread_comics(). Use it?
        unreads = self.unread_comic_set()
        # build a list of comic ids to later get the comics correctly ordered from all_comics
        comic_ids = list(set([unread.comic.id for unread in unreads]))
        comics = [comic for comic in self.subscribed_comics() if comic.id in comic_ids]
        unread_counters = dict()
        for unread in unreads:
            if unread.comic.id not in unread_counters.keys():
                unread_counters[unread.comic.id] = 1
            else:
                unread_counters[unread.comic.id] += 1
        return [(comic, unread_counters[comic.id]) for comic in comics]

    def unread_comic_strips(self, comic):
        """List of unread strips of a certain comic."""
        unreads = self.unread_comic_set().filter(comic__id=comic.id)
        return [unread.history for unread in unreads]

    def mark_comic_unread(self, comic):
        """Sets a comic as unread adding the last strip as unread for this user."""
        if self.user.is_subscribed(comic):
            strip = comic.last()
            if strip:
                self.user.unreadcomic_set.create(user=self.user, comic=comic, history=strip)
                return True
        return False

    def mark_comic_read(self, comic):
        """Mark the comic as read, removing the unread strips."""
        self.user.unreadcomic_set.filter(comic=comic).delete()

    def mark_all_read(self):
        """Mark all comics as read."""
        self.user.unreadcomic_set.all().delete()

    def unread_comic_strips_count(self, comic):
        """For a certain comic, how many unread strips does this user have?"""
        return self.unread_comic_set().filter(comic__id=comic.id).count()

    def unread_strips_count(self):
        """Total number of unread strips."""
        return self.unread_comic_set().count()

    # Subscriptions
    def subscribed_all(self):
        """Get a list of Subscriptions including inactive and ended."""
        # FUTURE: Should we return a list of Comic objects instead?
        return self.user.subscription_set.all()

    def subscribed_comics(self):
        """Get a list of Comic objects that the user is subscribed to."""
        # FUTURE: Should we return a list of Subscription objects instead?
        subscriptions = self.user.subscription_set.exclude(comic__active=False, comic__ended=False)
        return [s.comic for s in subscriptions]

    def is_subscribed(self, comic):
        """Check if the user is subscribed to a comic."""
        return self.user.subscription_set.filter(comic__id=comic.id).count() == 1

    def subscribe_comic(self, comic):
        """Subscribe the user to this comic, adding it last to his list."""
        if self.is_subscribed(comic):
            return
        # Calculate the position for the comic, it'll be the last
        max_position = self.user.subscription_set.aggregate(pos=Max('position'))['pos']
        if not max_position:
            # max_position can be None if there are no comics
            max_position = 0
        next_pos = max_position + 1
        self.user.subscription_set.create(comic=comic, position=next_pos)
        # Add the last strip to the user's unread list
        history = ComicHistory.objects.filter(comic=comic)
        if history:
            logger.debug("Found a strip to add")
            UnreadComic.objects.create(user=self.user, comic=comic, history=history[0])
        else:
            logger.debug("Did not add any strip to the user")

    def subscribe_comics(self, id_list):
        """Subscribe the user to all the comics in the list."""
        new_comics = Comic.objects.in_bulk(id_list)
        for comic in new_comics.values():
            self.subscribe_comic(comic)

    def unsubscribe_comic(self, comic):
        """Remove the comic from the user's subscriptions."""
        subscription = self.user.subscription_set.filter(comic=comic)
        if subscription:
            logger.debug("Removing subscription")
            subscription.delete()
            self.user.unreadcomic_set.filter(comic=comic).delete()
            self.user.newcomic_set.filter(comic=comic).delete()

    def unsubscribe_comics(self, id_list):
        """Remove the comics in the list from the user's subscriptions."""
        subscriptions = self.user.subscription_set.filter(comic__id__in=id_list)
        if subscriptions:
            logger.debug("Removing subscriptions")
            subscriptions.delete()
            self.user.unreadcomic_set.filter(comic__id__in=id_list).delete()
            self.user.newcomic_set.filter(comic__id__in=id_list).delete()

    def unsubscribe_all_comics(self):
        """Remove all of the user's subscriptions."""
        self.user.subscription_set.all().delete()
        self.mark_all_read()

    def random_comic(self):
        """Get a random ComicHistory of a Comic that the user is not following.

        The comic must be active and the ComicHistory returned must be the most recent."""
        subscribed_ids = [subscription.comic.id for subscription in self.subscribed_all()]
        not_subscribed_comics = list(active_comics().exclude(id__in=subscribed_ids))
        history = None
        if not_subscribed_comics:
            while not history:
                # Find the first not subscribed comic with a ComicHistory
                try:
                    random_comic = not_subscribed_comics[random.randint(0, len(not_subscribed_comics) - 1)]
                    history = random_comic.last_strip()
                except:
                    pass
        return history

    def new_comics(self):
        """Get the new comics for the user in a QuerySet."""
        return NewComic.objects.exclude(comic__active=False, comic__ended=False)

    def is_new(self, comic):
        """Is this comic new for the user?"""
        return NewComic.objects.filter(comic=comic, user=self.user).count() != 0

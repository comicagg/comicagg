# -*- coding: utf-8 -*-
import logging
import random
from django.db.models import Max
from comicagg.comics.models import Comic, ComicHistory, UnreadComic

logger = logging.getLogger(__name__)

class UserOperations(object):
    """This class allows operations with comic stuff and a certain user."""

    def __init__(self, user, **kwargs):
        super().__init__(**kwargs)
        self.user = user

    # Subscriptions

    def subscribed_all(self):
        """Get a list of Subscriptions including inactive and ended."""
        return self.user.subscription_set.all()

    def subscribed_comics(self):
        """Get a list of Comic objects that the user is subscribed to."""
        subscriptions = self.user.subscription_set.exclude(comic__activo=False, comic__ended=False)
        return [s.comic for s in subscriptions]

    def random_comic(self):
        """Get a random comic that the user is not following."""
        subscribed_ids = [comic.id for comic in self.subscribed_comics()]
        not_subscribed_comics = list(Comic.objects.exclude(id__in=subscribed_ids))
        history = None
        if not_subscribed_comics:
            try:
                random_comic = not_subscribed_comics[random.randint(0, len(not_subscribed_comics) - 1)]
                history_set = random_comic.comichistory_set.all()
                history = history_set[random.randint(0, len(history_set) - 1)]
            except:
                pass
        return history

    # Unreads

    def unread_comic_set(self):
        """Return the UnreadComic set for the user filtered."""
        return self.user.unreadcomic_set.exclude(comic__activo=False, comic__ended=False)

    def unread_comics(self):
        """Get a list of comics that have unread strips ordered by the position chosen by the user.
        
        Does not include the strips for each comic.
        """
        unreads = self.unread_comic_set()
        # Build a list of comic ids to later get the comics correctly ordered from all_comics
        comic_ids = list(set([u.comic.id for u in unreads]))
        return [c for c in self.subscribed_comics() if c.id in comic_ids]

    def unread_comics_count(self):
        """Get a list of tuples of comics with unread strips ordered by the position chosen by the user.

        First value is the comic, second is the number of unread strips.
        """
        unreads = self.unread_comic_set()
        # build a list of comic ids to later get the comics correctly ordered from all_comics
        comic_ids = list(set([u.comic.id for u in unreads]))
        comics = [c for c in self.subscribed_comics() if c.id in comic_ids]
        unread_counters = dict()
        for unread in unreads:
            if unread.comic.id not in unread_counters.keys():
                unread_counters[unread.comic.id] = 1
            else:
                unread_counters[unread.comic.id] += 1
        return [(c, unread_counters[c.id]) for c in comics]

    def unread_comic_strips(self, comic):
        """List of unread strips of a certain comic."""
        unreads = self.unread_comic_set().filter(comic__id=comic.id)
        return [u.history for u in unreads]

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

    # Subscribed comics

    def is_subscribed(self, comic):
        return self.user.subscription_set.filter(comic__id=comic.id).count() == 1

    def subscribe_comic(self, comic):
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
        new_comics = Comic.objects.in_bulk(id_list)
        for comic in new_comics.values():
            self.subscribe_comic(comic)

    def unsubscribe_comic(self, comic):
        s = self.user.subscription_set.filter(comic=comic)
        if s:
            logger.debug("Removing subscription")
            s.delete()
            self.user.unreadcomic_set.filter(comic=comic).delete()
            self.user.newcomic_set.filter(comic=comic).delete()

    def unsubscribe_comics(self, id_list):
        sx = self.user.subscription_set.filter(comic__id__in=id_list)
        if sx:
            logger.debug("Removing subscriptions")
            sx.delete()
            self.user.unreadcomic_set.filter(comic__id__in=id_list).delete()
            self.user.newcomic_set.filter(comic__id__in=id_list).delete()

    def unsubscribe_all_comics(self):
        self.user.subscription_set.all().delete()
        self.mark_all_read()

# -*- coding: utf-8 -*-
from comicagg.comics.models import Comic, ComicHistory, UnreadComic

class UserOperations(object):
    """This class allows operations with comic stuff and a certain user."""

    def __init__(self, user, **kwargs):
        super().__init__(**kwargs)
        self.user = user

    def all_comics(self):
        """List of all the comics the user is subscribed to."""
        subscriptions = self.user.subscription_set.exclude(comic__activo=False, comic__ended=False)
        return [s.comic for s in subscriptions]

    def random_comic(self):
        """Return a random comic that the user is not following."""
        comic_ids = [comic.id for comic in self.all_comics()]
        comics = list(Comic.objects.exclude(id__in=comic_ids))
        history = None
        if comics:
            try:
                comic = comics[random.randint(0, len(comics) - 1)]
                history = comic.comichistory_set.all()
                history = history[random.randint(0, len(history) - 1)]
            except:
                pass
        return history

    # Unread comics

    def unread_comics(self):
        """List of comics with unread strips ordered by the position chosen by the user.
        
        Does not include the strips for each comic.
        """
        unreads = self.user.unreadcomic_set.exclude(comic__activo=False, comic__ended=False)
        # Build a list of comic ids to later get the comics correctly ordered from all_comics
        comic_ids = list(set([u.comic.id for u in unreads]))
        return [c for c in self.all_comics() if c.id in comic_ids]

    def unread_comics_count(self):
        """List of tuples of comics with unread strips ordered by the position chosen by the user.

        First value is the comic, second is the number of unread strips.
        """
        unreads = self.user.unreadcomic_set.exclude(comic__activo=False, comic__ended=False)
        # build a list of comic ids to later get the comics correctly ordered from all_comics
        comic_ids = list(set([u.comic.id for u in unreads]))
        comics = [c for c in self.all_comics() if c.id in comic_ids]
        unread_counters = dict()
        for u in unreads:
            if u.comic.id not in unread_counters.keys():
                unread_counters[u.comic.id] = 1
            else:
                unread_counters[u.comic.id] += 1
        return [(c, unread_counters[c.id]) for c in comics]

    def unread_comic_strips(self, comic):
        """List of unread strips of a certain comic."""
        unreads = self.user.unreadcomic_set.exclude(comic__activo=False, comic__ended=False).filter(comic__id=comic.id)
        return [u.history for u in unreads]

    def mark_comic_unread(self, comic):
        """Sets a comic as unread adding the last strip as unread for this user."""
        if self.user.is_subscribed(comic):
            strip = comic.last()
            if strip:
                self.user.unreadcomic_set.create(user=self.user, comic=comic, history=strip)
                return True
        return False

    def unread_comic_strips_count(self, comic):
        """For a certain comic, how many unread strips does this user have?"""
        return self.user.unreadcomic_set.exclude(comic__activo=False, comic__ended=False).filter(comic__id=comic.id).count()

    def unread_strips_count(self):
        """Total number of unread strips."""
        return self.user.unreadcomic_set.exclude(comic__activo=False, comic__ended=False).count()

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

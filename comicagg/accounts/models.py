# -*- coding: utf-8 -*-
from comicagg.comics.models import Comic, ComicHistory, UnreadComic
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Max
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from datetime import datetime
import logging, random

logger = logging.getLogger(__name__)

# Create your models here.
class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)

    last_read_access = models.DateTimeField()
    new_comics = models.BooleanField(default=False)
    new_blogs = models.BooleanField(default=False)

    hide_read = models.BooleanField(default=True)
    #sort_by_points = models.BooleanField(default=False)

    alert_new_comics = models.BooleanField(default=True)
    alert_new_blog = models.BooleanField(default=True)

    navigation_max_columns = models.IntegerField(default=5)
    navigation_max_per_column = models.IntegerField(default=20)

    css_color = models.CharField(max_length=100, default="blue_white")

    def __unicode__(self):
        return u'%s' % self.user

    def is_active(self):
        if self.user.is_active:
            return True
        return False
    is_active.boolean = True

    class Meta:
        ordering = ['user']
        verbose_name = _('User profile')
        verbose_name_plural = _('User profiles')

    # Shortcut methods

    # A comic can be:
    # A active, E ended
    #   A T F
    # E
    # T   - 2
    # F   1 3
    # 1. Active AND not Ended - all ok, ongoing
    # 2. Not active AND Ended - finished
    # 3. Not active and not Ended - not working, needs fixing
    # So visible to the user should be 1 and 2

    def all_comics(self):
        """
        List of all the comics the user is subscribed to
        """
        subscriptions = self.user.subscription_set.exclude(comic__activo=False, comic__ended=False)
        return [s.comic for s in subscriptions]

    def unread_comics(self, count=False):
        """
        List of comics with unread strips ordered by the position chosen by the user.
        Does not include the strips for each comic.
        """
        unreads = self.user.unreadcomic_set.exclude(comic__activo=False, comic__ended=False)
        # build a list of comic ids to later get the comics correctly ordered from all_comics
        comic_ids = list(set([u.comic.id for u in unreads]))
        comics = [c for c in self.all_comics() if c.id in comic_ids]
        if not count:
            return comics
        unread_counters = dict()
        for u in unreads:
            if not u.comic.id in unread_counters.keys():
                unread_counters[u.comic.id] = 1
            else:
                unread_counters[u.comic.id] += 1
        return [(c, unread_counters[c.id]) for c in comics]


    def unread_comic_strips(self, comic):
        """
        List of unread strips of a certain comic
        """
        unreads = self.user.unreadcomic_set.exclude(comic__activo=False, comic__ended=False).filter(comic__id=comic.id)
        return [u.history for u in unreads]

    def unread_comic_strips_count(self, comic):
        """
        For a certain comic, how many unread strips does this user have?
        """
        return self.user.unreadcomic_set.exclude(comic__activo=False, comic__ended=False).filter(comic__id=comic.id).count()

    def unread_strips_count(self):
        """
        Total number of unread strips
        """
        return self.user.unreadcomic_set.exclude(comic__activo=False, comic__ended=False).count()

    def random_comic(self):
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

def create_account(sender, **kwargs):
    if kwargs['created']:
        up = UserProfile(user=kwargs['instance'], last_read_access=datetime.now())
        up.save()

post_save.connect(create_account, sender=User)

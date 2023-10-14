# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timezone

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


# Create your models here.
class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, on_delete=models.CASCADE)

    last_read_access = models.DateTimeField()
    new_comics = models.BooleanField(default=False)
    new_blogs = models.BooleanField(default=False)

    hide_read = models.BooleanField(default=True)
    # sort_by_points = models.BooleanField(default=False)

    alert_new_comics = models.BooleanField(default=True)
    alert_new_blog = models.BooleanField(default=True)

    navigation_max_columns = models.IntegerField(default=5)
    navigation_max_per_column = models.IntegerField(default=20)

    css_color = models.CharField(max_length=100, default="blue_white")

    class Meta:
        ordering = ["user"]
        verbose_name = _("User profile")
        verbose_name_plural = _("User profiles")

    def __str__(self):
        return "%s" % self.user

    def is_active(self):
        if self.user.is_active:
            return True
        return False

    is_active.boolean = True


def create_account(sender, **kwargs):
    if kwargs["created"]:
        up = UserProfile(
            user=kwargs["instance"], last_read_access=datetime.now(timezone.utc)
        )
        up.save()


post_save.connect(create_account, sender=User)

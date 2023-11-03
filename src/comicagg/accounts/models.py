import logging
from datetime import datetime, timezone

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, related_name="user_profile", on_delete=models.CASCADE
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


def create_account(sender, **kwargs):
    if kwargs["created"]:
        user_profile = UserProfile(
            user=kwargs["instance"], last_read_access=datetime.now(timezone.utc)
        )
        user_profile.save()


post_save.connect(create_account, sender=User)

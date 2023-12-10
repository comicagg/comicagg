import logging

from django.contrib.auth import models as auth_models
from django.db import models
from django.utils.translation import gettext_lazy as _
from comicagg.comics.managers import SubscriptionManager, UnreadStripManager

logger = logging.getLogger(__name__)


class User(auth_models.User):
    """Proxy class of the default's User class.
    Adds helper class methods."""

    unreadcomic_set: UnreadStripManager
    subscription_set: SubscriptionManager

    class Meta:
        proxy = True

    # Subscriptions
    def subscriptions(self):
        return self.subscription_set.available()

    # Unread strips
    def strips(self):
        """Return unread strips for this user."""
        return self.unreadcomic_set.available()


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

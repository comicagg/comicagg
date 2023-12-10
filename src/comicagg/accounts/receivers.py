from datetime import datetime, timezone

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User, dispatch_uid="post_save_create_profile")
def create_profile(sender, **kwargs):
    if kwargs["created"]:
        user_profile = UserProfile(
            user=kwargs["instance"], last_read_access=datetime.now(timezone.utc)
        )
        user_profile.save()

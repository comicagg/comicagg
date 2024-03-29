from datetime import datetime
from typing import Any

from django.db import models

from comicagg.accounts.models import User
from comicagg.comics.managers import (
    ComicManager,
    SubscriptionManager,
    UnreadStripManager,
)

class Comic(models.Model):
    class ComicStatus(models.IntegerChoices):
        INACTIVE = 0, "Inactive. Never shown"
        ACTIVE = 1, "Active"
        ENDED = 2, "Ended"
        BROKEN = 3, "Broken"

    objects: ComicManager = ...
    subscription_set: SubscriptionManager
    strip_set: models.BaseManager[Strip]

    id: int = ...
    name: str = ...
    website: str = ...
    status: int = ...
    no_images: bool = ...
    notify: bool = ...
    add_date: datetime = ...
    custom_func: str = ...
    re1_url: str = ...
    re1_base: str = ...
    re1_re: str = ...
    re1_backwards: bool = ...
    re2_url: str = ...
    re2_base: str = ...
    re2_re: str = ...
    re2_backwards: bool = ...
    referrer: str = ...
    last_update: datetime = ...
    last_update_status: str = ...
    last_image: str = ...
    last_image_alt_text: str = ...
    positive_votes: int = ...
    total_votes: int = ...

    last_strip: Strip = ...

    def get_rating(self) -> float: ...

class Subscription(models.Model):
    objects: SubscriptionManager = ...

    id: int = ...
    user: User = ...
    comic: Comic = ...
    position: int = ...

class Request(models.Model):
    id: int = ...
    user: User = ...
    url: str = ...
    comment: str = ...
    admin_comment: str = ...
    done: bool = ...
    rejected: bool = ...

class Strip(models.Model):
    id: int = ...
    comic: Comic = ...
    date: datetime = ...
    url: str = ...
    alt_text: str = ...

class UnreadStrip(models.Model):
    objects: UnreadStripManager = ...

    id: int = ...
    user: User = ...
    comic: Comic = ...
    strip: Strip = ...

class Tag(models.Model):
    id: int = ...
    user: User = ...
    comic: Comic = ...
    name: str = ...

class NewComic(models.Model):
    id: int = ...
    user: User = ...
    comic: Comic = ...

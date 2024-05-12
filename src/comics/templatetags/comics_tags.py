import contextlib

from django import template
from django.utils.translation import gettext as _

from ..models import Comic

register = template.Library()


@register.filter()
def as_percent(number, decimals=0):
    a_number = 0.0
    with contextlib.suppress(ValueError):
        a_number = float(number)
    return round(a_number * 100, decimals)


@register.filter()
def to_int(number):
    return int(number)


@register.filter()
def format_rating(comic: Comic):
    a_number = 0.0
    with contextlib.suppress(ValueError):
        a_number = float(comic.get_rating())
    return int(round(a_number * 100, 0))


@register.filter()
def unreads(comic: Comic, user_id):
    return comic.unreadstrip_set.filter(user=user_id)


@register.filter()
def equals(value, equals_to):
    return str(value) == equals_to


@register.simple_tag
def comic_list_tags(comic: Comic, user_comics: list[Comic], new_comics: list[Comic]):
    """Return the CSS classes for this comic."""
    tags = []
    if comic in user_comics:
        tags.append("added")
    if comic in new_comics:
        tags.append("new")
    if comic.is_broken():
        tags.append("broken")
    if comic.is_ended():
        tags.append("ended")
    return " ".join(tags)

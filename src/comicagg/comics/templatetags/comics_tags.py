import contextlib

from django import template
from django.utils.translation import gettext as _

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
def unreads(comic, user_id):
    return comic.unreadstrip_set.filter(user=user_id)

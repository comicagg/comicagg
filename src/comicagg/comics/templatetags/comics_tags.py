import contextlib
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.translation import gettext as _
from django.contrib.auth.models import User

from comicagg.comics.utils import ComicsService

register = template.Library()


@register.filter()
def as_percent(number, decimals=0):
    return round(float(number) * 100, decimals)


@register.filter()
def to_int(number):
    return int(number)


@register.filter()
def unreads(comic, user_id):
    return comic.unreadcomic_set.filter(user=user_id)

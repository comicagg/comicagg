from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from comicagg.blog.views import is_new_for
from django.utils.translation import ugettext as _

register = template.Library()

@register.filter()
def new(value, arg):
    """Returns whether a news item is new for a user or not.
    """
    return is_new_for(value, arg)

from comicagg.blog.views import is_new_for
from django import template

register = template.Library()


@register.filter()
def new(value, arg):
    """Returns whether a news item is new for a user or not."""
    return is_new_for(value, arg)

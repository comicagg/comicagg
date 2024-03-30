from django import template

from accounts.models import User

from ..models import NewBlog, Post

register = template.Library()


@register.filter()
def new(value, arg):
    """Returns whether a news item is new for a user or not."""
    return NewBlog.objects.filter(user=arg, post=value)

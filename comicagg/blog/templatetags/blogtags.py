from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from comic_ak.blog.views import is_new_for
from django.utils.translation import ugettext as _

register = template.Library()

@register.filter()
def new(value, arg):
  return is_new_for(value, arg)

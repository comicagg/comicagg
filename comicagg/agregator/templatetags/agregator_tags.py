# -*- coding: utf-8 -*-
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.translation import ugettext as _
#import math

register = template.Library()

@register.simple_tag
def is_new(comic, user):
    ret = ""
    if comic.is_new_for(user):
        ret = '<span id="new_comic' + str(comic.id) + '" class="new_comic">' + _("NEW!") + '&nbsp;</span>'
    return ret

@register.filter(name='recortar')
@stringfilter
def recortar(value, arg):
    n = int(arg)-3
    if len(value)<=n: return value
    m = n/2
    return '%s...%s' % (value[:m], value[len(value)-m:len(value)])

@register.filter(name='recortar2')
@stringfilter
def recortar2(value, arg):
    n = int(arg)-3
    if len(value)<=n: return value
    return '%s...' % (value[:n])

@register.filter()
def is_in(value, arg):
    ret = False
    try:
        arg.index(value)
        ret = True
    except:
        pass
    return ret

@register.filter()
def div(value, arg):
    try:
        return float(value)/arg
    except ZeroDivisionError:
        return 0

@register.filter(name='perc')
def perc(value, arg=0):
    return round(float(value) * 100, arg)

@register.filter()
def gt(value, arg):
    try:
        return int(value) > int(arg)
    except:
        return None

@register.filter()
def mult(value, arg):
    return float(value)*arg

@register.filter()
def toint(value):
    return int(value)

@register.filter()
def reverse(value):
    value.reverse()
    return value

class IsNewForUserNode(template.Node):
    def __init__(self, comic, user, context_var):
        self.comic = comic
        self.user = user
        self.context_var = context_var
    
    def render(self, context):
        comic = template.resolve_variable(self.comic, context)
        user = template.resolve_variable(self.user, context)
        
        context[self.context_var] = comic.is_new_for(user)
        return ''

def do_is_new_for_user(parser, token):
    """
    Example usage::
    {% is_new_for_user comic user as var %}
    """
    
    bits = token.contents.split()
    if len(bits) != 5:
        raise template.TemplateSyntaxError("'%s' tag takes exactly four arguments" % bits[0])
    if bits[3] != 'as':
        raise template.TemplateSyntaxError("second argument to '%s' tag must be 'as'" % bits[0])
    return IsNewForUserNode(bits[1], bits[2], bits[4])

register.tag('is_new_for_user', do_is_new_for_user)

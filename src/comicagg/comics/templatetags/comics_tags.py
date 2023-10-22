import contextlib
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.translation import gettext as _
from django.contrib.auth.models import User

from comicagg.comics.utils import ComicsService

register = template.Library()


@register.simple_tag
def is_new(comic, user: User):
    return (
        f'<span id="new_comic{str(comic.id)}" class="new_comic">{_("NEW!")}&nbsp;</span>'
        if ComicsService(user).is_new(comic)
        else ""
    )


@register.filter(name="recortar")
@stringfilter
def recortar(value, arg):
    n = int(arg) - 3
    value_len = len(value)
    if value_len <= n:
        return value
    m = n / 2
    return f"{value[:m]}...{value[value_len - m : value_len]}"


@register.filter(name="recortar2")
@stringfilter
def recortar2(value, arg):
    n = int(arg) - 3
    return value if len(value) <= n else f"{value[:n]}..."


@register.filter()
def is_in(value, arg):
    ret = False
    with contextlib.suppress(Exception):
        arg.index(value)
        ret = True
    return ret


@register.filter()
def div(value, arg):
    try:
        return float(value) / arg
    except ZeroDivisionError:
        return 0


@register.filter(name="perc")
def perc(value, arg=0):
    return round(float(value) * 100, arg)


@register.filter()
def gt(value, arg):
    try:
        return int(value) > int(arg)
    except Exception:
        return None


@register.filter()
def mult(value, arg):
    return float(value) * arg


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

        context[self.context_var] = user.operations.is_new(comic)
        return ""


def do_is_new_for_user(parser, token):
    """Example:
    {% is_new_for_user comic user as var %}
    """

    bits = token.contents.split()
    if len(bits) != 5:
        raise template.TemplateSyntaxError(
            f"'{bits[0]}' tag takes exactly four arguments"
        )
    if bits[3] != "as":
        raise template.TemplateSyntaxError(
            f"second argument to '{bits[0]}' tag must be 'as'"
        )
    return IsNewForUserNode(bits[1], bits[2], bits[4])


register.tag("is_new_for_user", do_is_new_for_user)


@register.filter()
def unreads(value, arg):
    """ "
    value is a comic
    arg is an user id
    """
    return value.unreadcomic_set.filter(user=arg)

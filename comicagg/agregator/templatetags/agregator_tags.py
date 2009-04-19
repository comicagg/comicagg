from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from comicagg.agregator.models import *
from comicagg.agregator.views import *
from django.utils.translation import ugettext as _
import math

register = template.Library()

@register.inclusion_tag('agregator/tag_cloud.html', takes_context=True)
def tagcloud_comic(context, comic):
  #hay que devolver un diccionario con el contexto para renderizar la plantilla
  from django.db import connection
  cursor = connection.cursor()
  cursor.execute("SELECT name, COUNT(name) FROM agregator_tag WHERE comic_id=%s GROUP BY name ORDER BY name ASC" % comic.id, [])
  tags_raw = cursor.fetchall()
  #tags = perc_func(tags_raw)
  tags = list()
  for tag in tags_raw:
    name, count = tag
    tags.append(TagWrap(name, count))
  calculate_cloud(tags)
  return { 'tags':tags, 'settings':context['settings']}
#registramos el tag para que renderice la plantilla que le digamos

@register.simple_tag
def user_tags(comic, user):
  tags = Tag.objects.filter(comic=comic, user=user)
  tag_list = list()
  for tag in tags:
    tag_list.append(tag.name)
  tags = ','.join(tag_list)
  return tags

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

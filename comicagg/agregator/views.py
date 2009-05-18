# -*- coding: utf-8 -*-
from django.db import IntegrityError
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from comicagg import *
from comicagg.agregator.models import *
from comicagg.agregator.check import check_comic
from comicagg.blog.models import NewBlog
from datetime import datetime
from django.utils.translation import ugettext as _
import sys, math, random

from django.views.decorators.cache import cache_page


# Create your views here.

@login_required
def read_view(request):
	if request.user and request.user.is_authenticated():
		try:
			up = request.user.get_profile()
			up.last_read_access=datetime.now()
			up.save()
		except:
			up = UserProfile(user=request.user, last_read_access=datetime.now())
			up.save()
		comic_list = list()
		unread_list_nav = list()
		has_unread = False
		sub_set = list(request.user.subscription_set.filter(comic__activo=True).filter(comic__ended=False))
		for subs in sub_set:
			l = request.user.unreadcomic_set.filter(comic=subs.comic)
			#repr(l)
			#triple = (objeto comic, lista de unread)
			triple = (subs.comic, l)
			if l:
				has_unread = True
			comic_list.append(triple)
			if l:
				unread_list_nav.append(triple)
		nmc = up.navigation_max_columns
		nmpc = up.navigation_max_per_column
		(comic_list_nav, items_per_column) = make_groups(comic_list, nmc, nmpc)
		(unread_list_nav, items_per_column) = make_groups(unread_list_nav, nmc, nmpc)
		#request.user.unreadcomic_set.all().delete()
		random = random_comic(request.user)
		context = {
			'comic_list':comic_list,
			'comic_list_nav':comic_list_nav,
			'unread_list_nav':unread_list_nav,
			'has_unread':has_unread,
			'items_per_column':items_per_column,
			'random_comic':random,
			'new_posts':NewBlog.objects.filter(user=request.user),
			'new_comic_count':NewComic.objects.filter(user=request.user).count(),
		}
		return render(request, 'agregator/read.html', context, 'read')

def random_comic(user, xhtml=False, request=None):
  not_in_list = Comic.objects.filter(activo=True).filter(ended=False).exclude(id__in=[s.comic.id for s in Subscription.objects.filter(user=user)])
  if not_in_list:
    try:
      comic = not_in_list[random.randint(0, len(not_in_list)-1)]
      history = comic.comichistory_set.all()
      history = history[random.randint(0, len(history)-1)]
    except:
      history = None
    if xhtml and history:
      return render(request, 'agregator/read_random.html', {'random_comic':history})
      #TODO
    return history
  return None

@login_required
def random_comic_view(request):
  user = request.user
  resp = random_comic(user, xhtml=True, request=request)
  if resp:
    return resp
  else:
    raise Http404

def make_groups(the_list, max_columns=5, max_per_column=20):
  groups = list()
  if the_list:
  #calcular cuantas columnas hay segun max_per_column
    size = len(the_list)
    columns = size / max_per_column
    if size % max_per_column != 0:
      columns += 1
  #mientras numero de columnas supere max_columns
  #aumentar en uno max_per_column y recalcular columnas
    while columns > max_columns:
      max_per_column += 1
      columns = size / max_per_column
      if size % max_per_column != 0:
        columns += 1
  #una vez tenemos el numero de columnas y max_per_column
  #separamos por grupos
    for i in range(columns):
      groups.append(the_list[i*max_per_column:i*max_per_column+max_per_column])
  return (groups, max_per_column)

@login_required
def configure(request, tag = None):
  context = {}
  #mostrar pagina de configuracion
  #build available list depending on not selected comics
  all_comics = set(Comic.objects.filter(activo=True).filter(ended=False))
  user_subs = request.user.subscription_set.all().filter(comic__activo=True).filter(comic__ended=False)
  user_comics = list()
  for sub in user_subs:
    user_comics.append(sub.comic)
  available = list()
  for comic in all_comics:
    if not comic in user_comics:
      available.append(comic)
  available.sort(comic_sort_name)
  if tag:
    available_list = list()
    #filter available list, show only ones with tag
    for comic in available:
      if comic.tag_set.filter(name=tag):
        available_list.append(comic)
    context['tag'] = tag
  else:
    available_list = available
  context['new_comics'] = NewComic.objects.filter(user=request.user).filter(comic__activo=True).filter(comic__ended=False)
  #add lists to context
  context['tags'] = get_full_tagcloud()
  context['available'] = available_list
  #quitar aviso de nuevos comics
  hide_new_comics(request)
  return render(request, 'agregator/configure.html', context, 'configure')

@login_required
def save_selection(request):
	if not request.POST:
		return HttpResponseForbidden('no')
	#get selection removing comic_ chars
	selection = request.POST['selected_list[]'].replace('comic_','').split(',')
	#remove duplicates
	selection_clean = list()
	for item in selection:
		if len(item)>0:
			#try to get an index, if it fails, item is not in the list so we append the item to the list
			try:
				selection_clean.index(int(item))
			except:
				selection_clean.append(int(item))
	#primero vemos qué comics nuevos se han elegido
	subscriptions = [s.comic.id for s in request.user.subscription_set.all()]
	nuevos = list()
	for s in selection_clean:
		if s not in subscriptions:
			nuevos.append(s)
	#comics que ahora no se seleccionan
	quitar = list()
	for s in subscriptions:
		if s not in selection_clean:
			quitar.append(s)
	#hay que quitar los unread de los comics que ya no leemos
	for cid in quitar:
		c = Comic.objects.get(pk=cid)
		request.user.unreadcomic_set.filter(comic=c).delete()
	#quitamos todas las suscripciones primero
	try:
		request.user.subscription_set.all().delete()
	except Exception, inst:
		return HttpResponse('-1')
	#si la seleccion esta vacia salimos
	if len(selection_clean)==0:
		return HttpResponse(_('Saved =)'))
	pos = 0
	for comic_id in selection_clean:
		c = Comic.objects.get(pk=comic_id)
		s = Subscription(user=request.user, comic=c, position=pos)
		s.save()
		#si es un comic nuevo lo marcamos como unread
		if c.id in nuevos:
			try:
				history = ComicHistory.objects.filter(comic=c)[0]
				u = UnreadComic(user=request.user, comic=c, history=history)
				u.save()
			except:
				pass
		try:
			#borra el objeto newcomic si hubiera
			n = NewComic.objects.get(user=request.user, comic=c)
			n.delete()
		except IntegrityError, (errno, errstr):
			#print "Subscription error %s: %s" % (errno, errstr)
			pass
		except Exception, inst:
			#print "***Unexpected error %s ***" % inst
			pass
		pos += 1
	if NewComic.objects.filter(user=request.user).count() == 0:
		up = request.user.get_profile()
		up.new_comics = False
		up.save()
	return HttpResponse(_('Saved =)'))

@login_required
def request_comic(request, done=False):
  context = {}
  if done:
    return render(request, 'agregator/request_comic_done.html', {}, 'configure')
  form = RequestForm()
  if request.POST:
    form = RequestForm(request.POST)
    if form.is_valid():
      url = form.cleaned_data['url']
      comment = form.cleaned_data['comment']
      req = Request(user=request.user, url=url, comment=comment)
      req.save()
      print type(req.comment)
      message = '%s\n%s\n%s' %(req.user, req.url, req.comment)
      send_mail('[CA] Nuevo request', message, 'Comic Aggregator <robot@comicagg.com>', ['admin@comicagg.com', 'korosu.itai@gmail.com'])
      return HttpResponseRedirect(reverse('done_request'))
  context['form'] = form
  context['count'] = Request.objects.all().count()
  return render(request, 'agregator/request_comic.html', context, 'configure')

@login_required
def get_tags(request):
  if not request.POST:
    return HttpResponseRedirect(reverse('configure'))
  comic_id = request.POST['id']
  comic = Comic.objects.get(pk=comic_id)
  tags = Tag.objects.filter(comic=comic, user=request.user)
  tag_list = list()
  for tag in tags:
    tag_list.append(tag.name)
  tags = ','.join(tag_list)
  return render(request, 'edit_tags_form.html', {'tags':tags})

@login_required
def save_tags(request):
  if not request.POST:
    return HttpResponseRedirect(reverse('configure'))
  comic_id = request.POST['id']
  tags = request.POST['tags']
  comic = Comic.objects.get(pk=comic_id)
  Tag.objects.filter(comic=comic, user=request.user).delete()
  for tag in tags.split(','):
    tag = tag.strip()
    if len(tag)>0:
      t = Tag.objects.get_or_create(comic=comic, user=request.user, name=tag.strip())
    #t.save()
  return render(request, 'agregator/tagging_form.html', {'tags':tags, 'comic':comic})

@login_required
def mark_read(request):
  if not request.POST:
    return HttpResponseRedirect(reverse('index'))
  comic_id = request.POST['id']
  comic = get_object_or_404(Comic, pk=comic_id)
  un = UnreadComic.objects.filter(user=request.user, comic=comic)
  un.delete()
  return HttpResponse('0')

@login_required
def report_comic(request):
  if not request.POST:
    raise Http404
  comic_id = int(request.POST['id'])
  comic = get_object_or_404(Comic, pk=comic_id)
  message = 'El usuario %s dice que hay una imagen rota en el comic %s\n' % (request.user, comic.name,)
  send_mail('[CA] Imagen rota', message, 'Comic Aggregator <robot@comicagg.com>', ['admin@comicagg.com', 'korosu.itai@gmail.com'])
  return HttpResponse('0')

@login_required
def mark_all_read(request):
  un = UnreadComic.objects.filter(user=request.user)
  un.delete()
  return HttpResponseRedirect(reverse('index'))

@login_required
def admin_check(request, comic_id=None):
  context = {}
  if request.user.is_staff:
    comic_list = Comic.objects.all().order_by('name')
    context['list'] = comic_list
    if comic_id:
      comic = Comic.objects.get(pk=comic_id)
      context['last'] = comic
      context['changed'] = check_comic(comic)
    context['title'] = _('Update comic')
    return render(request, 'admin/check.html', context)
  else:
    return HttpResponse("Nopes")

@cache_page(60*2)
def comic_list(request, sortby='name', tag=None):
  context = {}
  if tag:
    tags = Tag.objects.filter(name=tag)
    comics = list()
    for tag in tags:
      if tag.comic.activo and not tag.comic.ended:
        comics.append(tag.comic)
    comics = set(comics)
  else:
    comics = Comic.objects.filter(activo=True).filter(ended=False)
  comics = list(comics)
  if sortby=='rating':
    comics.sort(comic_sort_rating)
  elif sortby=='readers':
    comics.sort(comic_sort_readers)
  else:
    comics.sort(comic_sort_name)
  inactive_list = list(Comic.objects.filter(activo=False).filter(ended=False))
  ended_list = list(Comic.objects.filter(ended=True))
  inactive_list.sort(comic_sort_name)
  ended_list.sort(comic_sort_name)
  context = {
    'list':comics,
    'inactive_list':inactive_list,
    'ended_list':ended_list,
    'sortedby':sortby,
    'tag':tag,
    'tags':get_full_tagcloud(),
  }
  if request.user.is_authenticated():
    user_subs = request.user.subscription_set.all()
    user_comics = list()
    for sub in user_subs:
      user_comics.append(sub.comic)
    context['user_comics'] = user_comics
  return render(request, 'agregator/comic_list.html', context, menu='comic_list')

@login_required
def rate_comic(request):
  if request.POST:
    id = int(request.POST['id'])
    value = int(request.POST['value'])
    comic = get_object_or_404(Comic, pk=id)
    if value == -1:
      value = 0
    elif value == 1:
      value = 1
    else:
      raise Http404
    comic.rating += value
    comic.votes += 1
    comic.save()
    return HttpResponse("0")
  raise Http404

@login_required
def hide_new_comics(request):
  try:
    up = request.user.get_profile()
  except:
    up = UserProfile(user=request.user, last_read_access=datetime.now())
  up.new_comics = False;
  up.save()
  return HttpResponse("0")

@login_required
def forget_new_comic(request, comic_id=None):
	comic = get_object_or_404(Comic, pk=comic_id)
	NewComic.objects.filter(user=request.user, comic=comic).delete()
	count = str(NewComic.objects.filter(user=request.user).count())
	return HttpResponse(count)

@login_required
def forget_new_comics(request, quick=False):
	hide_new_comics(request)
	NewComic.objects.filter(user=request.user).delete()
	if quick:
		return HttpResponse('0')
	return HttpResponseRedirect(reverse('configure'))

@login_required
def add_comic(request, comic_id, next='comic_list'):
	comic = get_object_or_404(Comic, pk=comic_id)
	try:
		s = request.user.subscription_set.get(comic=comic)
	except:
		s = request.user.subscription_set.create(comic=comic, position=9999)
		#TODO añadir nuevo unread
		      #try:
        #history = ComicHistory.objects.filter(comic=c)[0]
        #u = UnreadComic(user=request.user, comic=c, history=history)
        #u.save()
      #except:
        #pass

	return HttpResponseRedirect(reverse(next))

@login_required
def remove_comic(request, comic_id):
  comic = get_object_or_404(Comic, pk=comic_id)
  s = request.user.subscription_set.get(comic=comic)
  s.delete()
  return HttpResponseRedirect(reverse('comic_list'))

@login_required
def add_comic_ajax(request):
	if request.POST:
		try:
			comic_id = int(request.POST['id'])
		except:
			comic_id = -1
		comic = get_object_or_404(Comic, pk=comic_id)
		try:
			s = request.user.subscription_set.get(comic=comic)
		except:
			s = request.user.subscription_set.create(comic=comic, position=9999)
		try:
			history = ComicHistory.objects.filter(comic=comic)[0]
			u = UnreadComic(user=request.user, comic=comic, history=history)
			u.save()
		except:
			pass
		return HttpResponse('0')
	raise Http404

@login_required
def remove_comic_ajax(request):
	if request.POST:
		try:
			comic_id = int(request.POST['id'])
		except:
			comic_id = -1
		comic = get_object_or_404(Comic, pk=comic_id)
		s = request.user.subscription_set.get(comic=comic)
		s.delete()
		return HttpResponse('0')
	raise Http404

#Funciones auxiliares
def get_full_tagcloud():
  #build tag cloud
  from django.db import connection
  cursor = connection.cursor()
  cursor.execute("SELECT name, COUNT(name) FROM agregator_tag GROUP BY name ORDER BY name ASC", [])
  tags_raw = cursor.fetchall()
  tags = list()
  for tag in tags_raw:
    name, count = tag
    tags.append(TagWrap(name, count))
  calculate_cloud(tags)
  return tags

def perc_func(tags_raw):
  tags = list()
  if not tags_raw:
    return tags
  maxc = 0
  minc = sys.maxint
  names = list()
  times = list()
  for name, count in tags_raw:
    if count > maxc:
      maxc = count
    if count < minc:
      minc = count
    names.append(name)
    times.append(count)

  (sd,mean) = stddev(times)
  sd -= 0.01
  for name, count in tags_raw:
    if count < settings.TAG_CLOUD_NUMBER:
      continue
    #perc = ((count/float(maxc)) * 100)
    #perc = ((count/float(minc)) * 100)
    factor = (count-mean)/sd

    if(factor <= -2 * sd):
      perc = 'xx-small'
    elif(factor <= -1 * sd):
      perc = 'x-small'
    elif(factor <= -0.5 * sd):
      perc = 'small'
    elif(factor <= 0.5 * sd):
      perc = 'medium'
    elif(factor <= 1 * sd):
      perc = 'large'
    elif(factor <= 2 * sd):
      perc = 'x-large'
    else:
      perc = 'xx-large'

    tags.append((name, perc))
  return tags

"""
esta función para ordenar devuelve los resultados al revés
para que se ordene de mayor a menor, en vez del modo normal que sería de menor a mayor
"""
def comic_sort_rating(x,y):
  if x.getRating() < y.getRating():
    return 1
  elif x.getRating() == y.getRating():
    ret = comic_sort_votes(x,y)
    if not ret:
      ret = comic_sort_readers(x,y)
    if not ret:
      ret = comic_sort_name(x,y)
    return ret
  return -1

#ascendente
def comic_sort_name(x,y):
  from django.template.defaultfilters import slugify
  a = slugify(x.name)
  b = slugify(y.name)
  if a<b:
    return -1
  elif a==b:
    return 0
  return 1

#mayor a menor
def comic_sort_readers(x,y):
  if x.subscription_set.count() < y.subscription_set.count():
    return 1
  elif x.subscription_set.count() == y.subscription_set.count():
    return 0
  return -1

#mayor a menor
def comic_sort_votes(x,y):
  if x.votes > y.votes:
    return -1
  elif x.votes == y.votes:
    return 0
  return 1

def mean(ns):
  n = len(ns)
  t = 0.0
  for x in ns:
    t += x
  return t / n

def stddev(ns):
  m = mean(ns)
  devs = list()
  for x in ns:
    devs.append((x - m) ** 2)
  md = mean(devs)
  return (math.sqrt(md), m)

#TAGS
class TagWrap:
  def __init__(self, name, count):
    self.name=name
    self.count=count
    self.font_size = 0

  def __unicode__(self):
    return u'%s, c=%d, fs=%d' %(self.name, self.count, self.font_size)

LINEAR, LOGARITHMIC = 1, 2

def _calculate_thresholds(min_weight, max_weight, steps):
  delta = (max_weight - min_weight) / float(steps)
  return [min_weight + i * delta for i in range(1, steps + 1)]

def _calculate_tag_weight(weight, max_weight, distribution):
  """
  Logarithmic tag weight calculation is based on code from the
  `Tag Cloud`_ plugin for Mephisto, by Sven Fuchs.

  .. _`Tag Cloud`: http://www.artweb-design.de/projects/mephisto-plugin-tag-cloud
  """
  if distribution == LINEAR or max_weight == 1:
    return weight
  elif distribution == LOGARITHMIC:
    return math.log(weight) * max_weight / math.log(max_weight)
  raise ValueError(_('Invalid distribution algorithm specified: %s.') % distribution)

def calculate_cloud(tags, steps=5, distribution=LOGARITHMIC):
  """
  Add a ``font_size`` attribute to each tag according to the
  frequency of its use, as indicated by its ``count``
  attribute.

  ``steps`` defines the range of font sizes - ``font_size`` will
  be an integer between 1 and ``steps`` (inclusive).

  ``distribution`` defines the type of font size distribution
  algorithm which will be used - logarithmic or linear. It must be
  one of ``tagging.utils.LOGARITHMIC`` or ``tagging.utils.LINEAR``.
  """
  if len(tags) > 0:
    counts = [tag.count for tag in tags]
    min_weight = float(min(counts))
    max_weight = float(max(counts))
    thresholds = _calculate_thresholds(min_weight, max_weight, steps)
    for tag in tags:
      font_set = False
      tag_weight = _calculate_tag_weight(tag.count, max_weight, distribution)
      for i in range(steps):
        if not font_set and tag_weight <= thresholds[i]:
          tag.font_size = i + 1
          font_set = True
  return tags

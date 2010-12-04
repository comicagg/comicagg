# -*- coding: utf-8 -*-
from comicagg import render
from comicagg.agregator.models import Comic, ComicHistory, NewComic, Request, RequestForm, Subscription, Tag
from comicagg.agregator.check import check_comic
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
import hashlib, math, os, random, sys, urllib2

from django.views.decorators.cache import cache_page

@login_required
def read_view(request):
    if request.user and request.user.is_authenticated():
        up = request.user.get_profile()
        up.last_read_access = datetime.now()
        up.save()
        comic_list = list()
        unread_list = list()
        unread_list_nav = list()
        has_unread = False
        sub_set = list(request.user.subscription_set.filter(comic__activo=True).filter(comic__ended=False))
        for subs in sub_set:
            l = request.user.unreadcomic_set.filter(comic=subs.comic)
            tup = (subs.comic, l)
            if l:
                has_unread = True
            comic_list.append(tup)
            if l:
                unread_list_nav.append(tup)
                unread_list.append(tup)
        nmc = up.navigation_max_columns
        nmpc = up.navigation_max_per_column
        (comic_list_nav, items_per_column) = make_groups(comic_list, nmc, nmpc)
        (unread_list_nav, items_per_column) = make_groups(unread_list_nav, nmc, nmpc)
        random = random_comic(request.user)
        context = RequestContext(request, {
            'comic_list':comic_list,
            'unread_list':unread_list,
            'comic_list_nav':comic_list_nav,
            'unread_list_nav':unread_list_nav,
            'has_unread':has_unread,
            'items_per_column':items_per_column,
            'random_comic':random,
            'new_blog_count':request.user.newblog_set.count(),
            'new_comic_count':request.user.newcomic_set.count(),
        })
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
            #TODO
            return render(request, 'agregator/read_random.html', {'random_comic':history})
        return history
    return None

@login_required
def random_comic_view(request):
    resp = random_comic(request.user, xhtml=True, request=request)
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
def organize(request, tag = None, add=False):
    context = {}
    #mostrar pagina de configuracion
    #build available list depending on not selected comics
    all_comics = list(Comic.objects.filter(activo=True).filter(ended=False))
    all_comics.sort(comic_sort_name)
    user_subs = request.user.subscription_set.all().filter(comic__activo=True).filter(comic__ended=False)
    user_comics = list()
    user_comics_id = list()
    for sub in user_subs:
        user_comics.append(sub.comic)
        user_comics_id.append(sub.comic.id)
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
    context['user_comics'] = user_comics
    context['all_comics'] = all_comics
    if add:
        #quitar aviso de nuevos comics
        hide_new_comics(request)
        template = 'agregator/organize_add.html'
    else:
        template = 'agregator/organize_organize.html'
    return render(request, template, context, 'configure')

@login_required
def request_index(request, ok=False):
    if request.POST:
        form = RequestForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            comment = form.cleaned_data['comment']
            req = Request(user=request.user, url=url, comment=comment)
            req.save()
            message = '%s\n%s\n%s' %(req.user, req.url, req.comment)
            send_mail('[CA] Nuevo request', message, 'Comic Aggregator <robot@comicagg.com>', ['admin@comicagg.com', 'korosu.itai@gmail.com'])
            return redirect('request_ok')
    else:
        form = RequestForm()
    context = {}
    context['form'] = form
    context['count'] = Request.objects.all().count()
    context['request_saved'] = ok
    context['accepted'] = request.user.request_set.filter(done__exact=1).filter(rejected__exact=0)
    context['rejected'] = request.user.request_set.filter(rejected__exact=1)
    context['pending'] = request.user.request_set.filter(done__exact=0).filter(rejected__exact=0)
    return render(request, 'agregator/request_index.html', context)

@login_required
def get_tags(request):
    if not request.POST:
        return redirect('configure')
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
        return redirect('configure')
    comic_id = request.POST['id']
    tags = request.POST['tags']
    comic = Comic.objects.get(pk=comic_id)
    Tag.objects.filter(comic=comic, user=request.user).delete()
    for tag in tags.split(','):
        tag = tag.strip()
        if len(tag) > 0:
            Tag.objects.get_or_create(comic=comic, user=request.user, name=tag.strip())
            #t.save()
    return render(request, 'agregator/tagging_form.html', {'tags':tags, 'comic':comic})

@login_required
def admin_check(request, comic_id=None):
    context = {}
    if request.user.is_staff:
        comic_list = Comic.objects.all().order_by('name')
        comic_dict = dict()
        for c in comic_list:
                l = c.name[0].upper()
                if l in comic_dict.keys():
                        comic_dict[l].append(c)
                else:
                        comic_dict[l] = [c]
        context['list'] = comic_dict
        if comic_id:
            comic = Comic.objects.get(pk=comic_id)
            context['last'] = comic
            context['changed'] = check_comic(comic)
        context['title'] = _('Update comic')
        return render(request, 'admin/check.html', context)
    raise Http404

def admin_reported(request, chids):
    context = {}
    if request.user.is_staff:
        chids = chids.split('-')
        chs = dict()
        for chid in chids:
            try:
                ch = ComicHistory.objects.get(pk=int(chid))
            except:
                ch = None
            chs[chid]= ch
        context['chs'] = chs
        return render(request, 'admin/reported.html', context)
    raise Http404

@cache_page(60*10)
def comic_list_load(request):
    if request.POST:
            cid = int(request.POST['id']);
            comic = get_object_or_404(Comic, pk=cid)
            context = {}
            context['comic'] = comic
            #si es un usuario registrado, coger su lista de comics
            if request.user.is_authenticated():
                    user_subs = request.user.subscription_set.all()
                    user_comics = list()
                    for sub in user_subs:
                            user_comics.append(sub.comic)
                            context['user_comics'] = user_comics
            return render(request, 'agregator/comic_list_comic.html', context, xml=True)
    return Http404()

@cache_page(60*10)
def comic_list(request, sortby='name', tag=None):
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

"""
Oculta el aviso de nuevos comics
"""
@login_required
def hide_new_comics(request):
    up = request.user.get_profile()
    up.new_comics = False;
    up.save()
    return HttpResponse("0")

@login_required
def forget_new_comics(request, quick=False):
    hide_new_comics(request)
    NewComic.objects.filter(user=request.user).delete()
    if quick:
        return HttpResponse('0')
    return redirect('configure')

def stats(request):
    """
    Genera una página de estadísticas para cada comic ordenada según la puntuación de cada comic
    """
    comics = list(Comic.objects.all())
    comics.sort(sort_rate)
    return render(request, 'stats.html', {'comics':comics})

def last_image_url(request, cid):
    """
    Redirecciona a la url de la ultima imagen de  un comic
    """
    comic = get_object_or_404(Comic, pk=cid)
    url = comic.last_image
    ref = comic.referer
    return image_url(url, ref)

def history_image_url(request, hid):
    """
    Redirecciona a la url de un objeto comic_history
    """
    ch = get_object_or_404(ComicHistory, pk=hid)
    url = ch.url
    ref = ch.comic.referer
    return image_url(url, ref)

def image_url(url, ref):
    md5 = hashlib.md5(url).hexdigest()
    ldst = os.path.join(settings.MEDIA_ROOT, 'strips', md5)
    dst = ldst
    if not os.path.exists(ldst):
        #the link doesnt exist, download the image
        dst = download_image(url, ref, dst)
        if dst:
            #the download went ok, we get the filename back
            os.symlink(dst, ldst)
        else:
            #the download returned None? better return a 500
            return HttpResponseServerError()
    return HttpResponseRedirect(settings.MEDIA_URL + 'strips/' + md5)

def download_image(url, ref, dest):
    headers = {
        'referer':ref,
        'user-agent':'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.342.7 Safari/533.2'
    }
    r = urllib2.Request(url, None, headers)
    o = urllib2.urlopen(r)
    ct = o.info()['Content-Type']
    if ct.startswith("image/"):
        #we got an image, thats good
        ext = ct.replace("image/", "")
        dest += "." + ext
    else:
        #no image mime? not cool
        return None

    f = open(dest, 'w+b')
    f.writelines(o.readlines())
    f.close()
    return dest

#Funciones auxiliares
def sort_rate(a,b):
    """
    Ordenar únicamente por la puntuación de los comics
    """
    c = b.getRating() - a.getRating()
    if c > 0: return 1
    elif c < 0: return -1
    else: return 0

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

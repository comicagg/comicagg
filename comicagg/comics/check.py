# -*- coding: utf-8 -*-
from comicagg.comics.models import ComicHistory, UnreadComic, NoMatchException
from datetime import datetime
from django.conf import settings
from html import unescape
import re
import requests

"""
Functions to check if the comics have been updated.
"""

def check_comic(comic):
    #lo que devolvemos para indicar que se ha actualizado el comic
    changes = False
    #si el campo custom_func está tenemos una funcion personalizada
    if comic.custom_func:
        changes = custom_check(comic)
    else:
        h = default_check(comic)
        if h:
            notify_subscribers(h)
            changes = True
    return changes

def custom_check(comic):
    #la funcion custom debe rellenar este array con los history de las nuevas
    #tiras
    history_set = list()
    f = comic.custom_func.replace('\r', '')
    code = compile(f, '<string>', 'exec')
    exec(code)
    #si se han encontrado imagenes
    if history_set:
        #comprobar si son nuevas
        if comic.last_image == history_set[0].url:
            return False
        #actualizar last_image y last_image_alt_text
        comic.last_image = history_set[0].url
        comic.last_image_alt_text = history_set[0].alt_text
        comic.last_check = datetime.now()
        comic.save()
        #llegado este punto, estamos seguros que son nuevas tiras, guardamos y
        #notificamos
        for h in history_set:
            h.save()
            notify_subscribers(h)
        return True
    #no se ha encontrado ninguna imagen, lanzar excepcion
    raise NoMatchException("%s" % comic.name)

def default_check(comic):
    #si hay redireccion, obtener url de la redireccion
    if comic.url2:
        next_url = getredirect(comic)
    else:
        next_url = comic.url

    #buscar url en la web que contiene la tira
    (last_image, alt) = getoneurl(comic, next_url)
    #en este punto last_image debe estar completamente saneada, es decir
    #si tiene entidades html, éstas pasadas a sus caracteres correspondientes
    #y a continuación el url debe estar urlencoded
    if last_image == comic.last_image:
        return None
    comic.last_image = last_image
    comic.last_image_alt_text = alt
    comic.last_check = datetime.now()
    h = ComicHistory(comic=comic, url=comic.last_image, alt_text=alt)
    h.save()
    comic.save()
    return h

def severalinpage(comic, history_set):
    lineas = open_url(comic, comic.url)
    #for check comic debugging
    lineas_o = list(lineas)
    (match, lineas) = match_lines(comic, lineas, comic.regexp, comic.backwards)
    while match:
        url = comic.base_img % geturl(match)
        alt = getalt(match)
        h = ComicHistory(comic=comic, url=url, alt_text=alt)
        history_set.append(h)
        (match, lineas) = match_lines(comic, lineas, comic.regexp, comic.backwards)

# Auxiliary functions needed to check for updates
def open_url(comic, _url):
    # Clean the URL
    url = unescape(_url)

    # NOTE: why did we need the cookie jar before?
    headers = {'User-Agent': settings.USER_AGENT}
    r = requests.get(url, headers=headers)
    lines = [line for line in r.iter_lines()]

    return lines

def match_lines(comic, lineas, regexp, backwards=False):
    indice = 0
    #si hay que empezar desde el final a buscar
    if backwards:
        indice = -1
    #compilar regexp
    rege = r'%s' % regexp
    prog = re.compile(rege)
    #search in every line for the regexp
    match = None
    while len(lineas) > 0:
        linea = lineas.pop(indice)
        try:
            linea = linea.decode('utf-8')
        except:
            pass
        match = prog.search(linea)
        if match:
            break
    return (match, lineas)

def getoneurl(comic, _url):
    lineas = open_url(comic, _url)
    #for check comic debugging
    lineas_o = list(lineas)
    (match, lineas) = match_lines(comic, lineas, comic.regexp, comic.backwards)
    if not match:
        raise NoMatchException("%s" % comic.name)
    url = comic.base_img % geturl(match)#.decode("utf-8")
    #coger el texto alternativo
    alt = getalt(match)
    return (url, alt)

def getredirect(comic):
    lineas = open_url(comic, comic.url2)
    #for check comic debugging
    lineas_o = list(lineas)
    (match, lineas) = match_lines(comic, lineas, comic.regexp2, comic.backwards2)
    if not match:
        raise NoMatchException("%s" % comic.name)
    next_url = comic.base2 % geturl(match)#.decode("utf-8")
    return next_url

def geturl(match):
    try:
        url = match.group("url")
    except IndexError:
        url = match.group(1)
    #devolver la url sin entidades html
    return unescape(url)

def getalt(match):
    try:
        alt = match.group("alt")
    except IndexError:
        alt = None
    if alt:
        try:
            alt = unicode(alt, 'utf-8')
        except:
            try:
                alt = unicode(alt, 'iso-8859-1')
            except:
                pass
    return alt

def notify_subscribers(history):
    #por cada usuario que ha seleccionado el comic, añadir un unread
    subscriptions = history.comic.subscription_set.all()
    for subscription in subscriptions:
        if subscription.user.is_active:
            UnreadComic.objects.get_or_create(user=subscription.user, history=history, comic=subscription.comic)

##
# Removes HTML or XML character references and entities from a text string.
# from http://effbot.org/zone/re-sub.htm#unescape-html
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.
def unescape_old(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

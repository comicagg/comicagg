#coding: utf-8
from comicagg.agregator.models import *
import re, sys, urllib2

def match_url(url=None, regexp=None, fake_user_agent=False, backwards=False):
  if not url or not regexp:
    return None
  r = urllib2.Request(url)
  if fake_user_agent:
    r.add_header('User-Agent', 'Firefox/3.0.1')
  #obtener url
  #respuesta = urllib2.urlopen(url)
  #lineas = respuesta.readlines()
  opener = urllib2.build_opener()
  respuesta = opener.open(r)
  lineas = respuesta.readlines()
  if backwards:
    lineas.reverse()
  respuesta.close()
  #compilar regexp
  rege = r'%s' % regexp
  prog = re.compile(rege)
  #search in every line for the regexp
  matched = False
  for linea in lineas:
    try:
      linea = linea.decode('utf-8')
    except:
      pass
    match = prog.search(linea)
    if match:
      matched = True
      break
  if not matched:
    raise NoMatchException, ''
  return match

def check_comic(comic=None):
  if not comic:
    return None

  #si hay redireccion, obtener url de la redireccion
  if comic.url2:
    match = match_url(comic.url2, comic.regexp2, fake_user_agent=comic.fake_user_agent, backwards=comic.backwards2)
    try:
      url = match.group("url")
    except IndexError:
      url = match.group(1)
    next_url = comic.base2 % url#.decode("utf-8")
  else:
    next_url = comic.url

  #buscar url en la web que contiene la tira
  match = match_url(next_url, comic.regexp, fake_user_agent=comic.fake_user_agent, backwards=comic.backwards2)
  try:
    url = match.group("url")
  except IndexError:
    url = match.group(1)
  last_image = comic.base_img % url#.decode("utf-8")
  #print ' fetched img %s' % last_image
  #en este punto last_image debe estar completamente saneada, es decir
  #si tiene entidades html, éstas pasadas a sus caracteres correspondientes
  #y a continuación el url debe estar urlencoded
  if last_image == comic.last_image:
    return None
  comic.last_image = last_image
  #print u' new img %s' % self.last_image
  comic.last_check = datetime.now()
  h = ComicHistory(comic=comic, url=comic.last_image)
  h.save()
  comic.save()
  return h

import re, htmlentitydefs

##
# Removes HTML or XML character references and entities from a text string.
# from http://effbot.org/zone/re-sub.htm#unescape-html
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
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
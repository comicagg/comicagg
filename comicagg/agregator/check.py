# -*- coding: utf-8 -*-
from comicagg.agregator.models import *
import re, sys, urllib2

def open_url(comic, _url):
	#limpiar la url (entidades html)
	url = unescape(_url)
	r = urllib2.Request(url)
	if comic.fake_user_agent:
		r.add_header('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.0.7) Gecko/2009030814 Firefox/3.0.5 (Debian-3.0.7-1)')
	#obtener url
	#respuesta = urllib2.urlopen(url)
	#lineas = respuesta.readlines()
	opener = urllib2.build_opener()
	respuesta = opener.open(r)
	lineas = respuesta.readlines()
	return lineas

def match_lines(comic, lineas, regexp, backwards=False):
	indice = 0
	#si hay que empezar desde el final a buscar
	if backwards:
		indice = -1
	#compilar regexp
	rege = r'%s' % regexp
	prog = re.compile(rege)
	#search in every line for the regexp
	while len(lineas) > 0:
		_linea = lineas.pop(indice)
		try:
			linea = _linea.decode('utf-8')
		except:
			pass
		match = prog.search(linea)
		if match:
			break
	if not match:
		raise NoMatchException, "%s" % comic.name
	return (match, lineas)

def custom_check(comic):
	#la funcion custom debe rellenar este array con los history de las nuevas tiras
	history_set = list()
	f = comic.custom_func
	exec(f)
	for h in history_set:
		notifiy_subscribers(h)
	if history_set:
		return True
	return false

def default_check(comic):
	#si hay redireccion, obtener url de la redireccion
	if comic.url2:
		lineas = open_url(comic, comic.url2)
		(match, rest) = match_lines(comic, lineas, comic.regexp2, comic.backwards2)
		try:
			url = match.group("url")
		except IndexError:
			url = match.group(1)
			next_url = comic.base2 % url#.decode("utf-8")
	else:
		next_url = comic.url

	#buscar url en la web que contiene la tira
	lineas = open_url(comic, next_url)
	(match, rest) = match_lines(comic, lineas, comic.regexp, comic.backwards)
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

def notifiy_subscribers(history):
	#por cada usuario que ha seleccionado el comic, añadir un unread
	subscriptions = history.comic.subscription_set.all()
	for subscription in subscriptions:
		unread = UnreadComic.objects.get_or_create(user=subscription.user, history=history, comic=subscription.comic)

def check_comic(comic):
	#lo que devolvemos para indicar que se ha actualizado el comic
	changes = False
	#si el campo custom_func está tenemos una funcion personalizada
	if comic.custom_func:
		changes = custom_check(comic)
	else:
		h = default_check(comic)
		if h:
			notifiy_subscribers(h)
			changes = True
	return changes

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

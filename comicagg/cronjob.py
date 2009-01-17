#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
from traceback import *
from datetime import datetime
import settings_local

sys.path.insert(0, settings_local.ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = "comicagg.settings"

from comicagg.agregator.models import *
from comicagg import send_email
from comicagg.agregator.check import check_comic

print "Hora comienzo: %s" % datetime.now()
print "Sólo se muestran errores de comics activos:"
#check all comics
all = Comic.objects.all()
new = 0
no_change = 0
errors = 0
for comic in all:
  #check for new strip
  try:
    h_obj = check_comic(comic)
  except NoMatchException:
    if comic.activo:
      print "Error comprobando %s" % comic
      print
    errors += 1
    continue
  except KeyboardInterrupt:
    print "Matado"
    sys.exit()
  except:
    #print_exc()
    if comic.activo:
      print "Error inesperado (", comic.name.encode('utf-8'), "):", sys.exc_info()[0], sys.exc_info()[1]
      print
    errors += 1
    #raise
    continue
  if h_obj:
    new += 1
    #foreach user who has a subscription, create the unreadcomic object
    subscriptions = comic.subscription_set.all()
    for subscription in subscriptions:
      unread = UnreadComic.objects.get_or_create(user=subscription.user, history=h_obj, comic=subscription.comic)
    #si es un comic desactivado o terminado y se actualiza notificar posible activacion
    if not comic.activo or comic.ended:
      message = 'El desactivado o terminado %s se ha actualizado.\n' % (comic.name,)
      details = {
        'to':'admin@comicagg.com',
        'from':'Comic Aggregator',
        'subject':"[CA] Comic desactivado actualizado",
        'message':message
      }
      send_email(details)
  else:
    no_change += 1

print "%s nuevos, %s sin cambios, %s errores" % (new, no_change, errors)
print "Hora fin: %s" % datetime.now()
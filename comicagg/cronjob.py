#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
from traceback import *
from datetime import datetime
import settings_local

sys.path.insert(0, settings_local.ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = "comicagg.settings"

from comicagg.agregator.models import *
from django.core.mail import send_mail
from comicagg.agregator.check import check_comic

print "Hora comienzo: %s" % datetime.now()
#check all comics
all = Comic.objects.all()
new = 0
no_change = 0
errors_active = list()
errors_inactive = list()
for comic in all:
  #check for new strip
  try:
    h_obj = check_comic(comic)
  except NoMatchException:
    s = "  Error comprobando %s" % comic
    if comic.activo:
      errors_active.append(s)
    else:
      errors_inactive.append(s)
    continue
  except KeyboardInterrupt:
    print "Matado"
    sys.exit()
  except:
    #print_exc()
    s = "  Error inesperado %s: %s" % (comic.name.encode('utf-8'), sys.exc_info()[1])
    if comic.activo:
      errors_active.append(s)
    else:
      errors_inactive.append(s)
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
      #send_mail('[CA] Comic desactivado actualizado', message, 'Comic Aggregator <robot@comicagg.com>', ['admin@comicagg.com'])
  else:
    no_change += 1

print "Comics activos"
for s in errors_active:
  print s

print "-------------------------"
print "Comics desactivados"
for s in errors_inactive:
  print s

print "%s nuevos, %s sin cambios, %s errores" % (new, no_change, (len(errors_active)+len(errors_inactive)))
print "Hora fin: %s" % datetime.now()

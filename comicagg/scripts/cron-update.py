#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
actualiza los comics
"""
import os, sys, threading, time
from traceback import *
from datetime import datetime
d=os.path.dirname(os.path.abspath(sys.argv[0]))
d=os.path.join(d, '..')
d=os.path.abspath(d)
sys.path.insert(0, d)

from scripts import is_running, not_running_anymore
is_running()

import settings_local
sys.path.insert(0, settings_local.ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = "comicagg.settings"

from comicagg.agregator.models import *
from django.core.mail import mail_managers
from comicagg.agregator.check import check_comic

#check all comics
all = list(Comic.objects.all())
new = 0
no_change = 0
errors = 0
updated_comics = list()
errors_active = list()
errors_inactive = list()
errors_unexpected = list()
inactive_updated = list()

class CheckThread(threading.Thread):
	def __init__(self, all, errors_active, errors_inactive):
		threading.Thread.__init__(self)
		self.all = all
		self.errors_active = errors_active
		self.errors_inactive = errors_inactive
		self.errors_unexpected = errors_unexpected
		self.inactive_updated = inactive_updated
		self.updated_comics = updated_comics

	def run(self):
		global new
		global no_change
		global errors

		comic = self.next()
		while comic:
			changed = False
			try:
				changed = check_comic(comic)
			except KeyboardInterrupt:
				print '*** Matado %s ***' % datetime.now()
				sys.exit()
			except NoMatchException:
				s = '   Error comprobando %s\n' % comic.name
				if comic.activo:
					self.errors_active.append(s)
				else:
					self.errors_inactive.append(s)
				errors += 1
				#continue
			except:
				#print_exc()
				s = '   Error inesperado %s: %s\n' % (comic.name, sys.exc_info()[1])
				if comic.activo:
					self.errors_unexpected.append(s)
				else:
					self.errors_inactive.append(s)
				errors += 1
				#raise
				#continue
			if changed:
				new += 1
				#si es un comic desactivado o terminado y se actualiza notificar posible activacion
				if not comic.activo or comic.ended:
					s = '   El desactivado o terminado %s se ha actualizado.\n' % comic.name
					self.inactive_updated.append(s)
				else:
					s = '   Actualizado %s\n' % comic.name
					updated_comics.append(s)
			else:
				no_change += 1
			comic = self.next()

	def next(self):
		print "%s: %d left, %d errors" % (self.getName(), len(self.all), errors)
		if len(self.all):
			return self.all.pop(0)

print '\n*** Ejecución de cronjob.py (%s) ***' % datetime.now()

salida = "Hora comienzo: %s\n" % datetime.now()
thread_list = list()
for i in xrange(5):
	t = CheckThread(all, errors_active, errors_inactive)
	thread_list.append(t)
	t.start()

for t in thread_list:
	t.join()

salida += "Errores en comics activos\n"
for s in errors_active:
	salida += s
salida += "-------------------------\n"
salida += "Errores inesperados en comics activos\n"
for s in errors_unexpected:
	salida += s
salida += "-------------------------\n"
salida += "Comics desactivados actualizados\n"
for s in inactive_updated:
	salida += s
salida += "-------------------------\n"
salida += "Errores en comics desactivados\n"
for s in errors_inactive:
	salida += s

salida += "Comics actualizados\n"
for s in updated_comics:
	salida += s
salida += "-------------------------\n"

salida += "%s nuevos, %s sin cambios, %s errores\n" % (new, no_change, (len(errors_active)+len(errors_inactive)+len(errors_unexpected)))
salida += "Hora fin: %s\n" % datetime.now()

try:
	mail_managers('Salida de cron', salida)
except:
	print "Got error sending email"
	print_exc()
	
print salida.encode("utf-8")
not_running_anymore()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.abspath('..'))
import settings_local
sys.path.insert(0, settings_local.ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = "comicagg.settings"

from comicagg.agregator.models import *
from django.contrib.auth.models import User

starttime = datetime.now()
if len(sys.argv) > 1:
	uid = int(sys.argv[1])
	allusers = User.objects.order_by('id').filter(id__gte = uid)
else:
   allusers = User.objects.all()
for user in allusers:
	now = datetime.now()-starttime
	if now.seconds > 3000:
		print "FIN: id=", user.id
		sys.exit()
	print user
	subs = user.subscription_set.all()
	for sub in subs:
		unreads = UnreadComic.objects.filter(user__exact=user).filter(comic__exact=sub.comic).order_by('-id')
		if unreads.count() > 50:
			sid = unreads[50].id
			print "", sub.comic
			deletes = UnreadComic.objects.filter(user__exact=user).filter(comic__exact=sub.comic).order_by('-id').filter(id__lte=sid)
			deletes.delete()
	time.sleep(0.5)

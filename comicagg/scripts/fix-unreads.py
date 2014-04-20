#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Borra unreadcomics de comics a los que no se esta suscrito
"""
import os, sys, time
from datetime import datetime
d=os.path.dirname(os.path.abspath(sys.argv[0]))
d=os.path.join(d, '..')
d=os.path.abspath(d)
sys.path.insert(0, d)
import settings_local
sys.path.insert(0, settings_local.ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = "comicagg.settings"

from comicagg.comics.models import *
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
	comics = []
	for sub in subs:
		comics.append(sub.comic.id)

	unreads = UnreadComic.objects.filter(user__exact=user).exclude(comic__in=comics)
	unreads.delete()
	time.sleep(0.5)

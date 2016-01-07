#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix: deletes unread comics for comics that the user is not subscribed to
"""
import os, sys, time
from datetime import datetime
# Add the root folder to the python path
d = os.path.dirname(os.path.abspath(sys.argv[0]))
d = os.path.join(d, '..')
d = os.path.join(d, '..')
d = os.path.abspath(d)
sys.path.insert(0, d)

os.environ['DJANGO_SETTINGS_MODULE'] = "comicagg.settings"

import django
django.setup()

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
        print("Ending: continue from ID=%s" % user.id)
        sys.exit()
    print(user)
    subs = user.subscription_set.all()
    comics = []
    for sub in subs:
        comics.append(sub.comic.id)

    unreads = UnreadComic.objects.filter(user__exact=user).exclude(comic__in=comics)
    unreads.delete()
    time.sleep(0.5)

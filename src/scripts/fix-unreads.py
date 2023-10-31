#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fixing script: deletes unread comics for comics that the user is not subscribed to."""
import os
import sys
import time
from datetime import datetime, timezone
# Add the root folder to the python path
# d = os.path.dirname(os.path.abspath(sys.argv[0]))
# d = os.path.join(d, '..')
# d = os.path.join(d, '..')
# d = os.path.abspath(d)
# sys.path.insert(0, d)

os.environ['DJANGO_SETTINGS_MODULE'] = "comicagg.settings"

import django
django.setup()

from django.contrib.auth.models import User
from comicagg.comics.models import UnreadComic

start_time = datetime.now(timezone.utc)
if len(sys.argv) > 1:
    uid = int(sys.argv[1])
    all_users = User.objects.order_by('id').filter(id__gte=uid)
else:
    all_users = User.objects.all()
for user in all_users:
    now = datetime.now(timezone.utc) - start_time
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

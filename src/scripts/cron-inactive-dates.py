#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""If a user is inactive, report it here.

The threshold to be considered inactive is settings.INACTIVE_DAYS
"""
import os
import sys
from datetime import datetime, timedelta, timezone
# Add the root folder to the python path
# d = os.path.dirname(os.path.abspath(sys.argv[0]))
# d = os.path.join(d, '..')
# d = os.path.join(d, '..')
# d = os.path.abspath(d)
# sys.path.insert(0, d)

os.environ['DJANGO_SETTINGS_MODULE'] = "comicagg.settings"

import django
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from comicagg.accounts.utils import get_profile

start_time = datetime.now(timezone.utc)
if len(sys.argv) > 1:
    uid = int(sys.argv[1])
    users = User.objects.order_by('id').filter(id__gte=uid).filter(is_active__exact=1)
else:
    users = User.objects.filter(is_active__exact=1)
limit = datetime.today() - timedelta(settings.INACTIVE_DAYS)
for user in users:
    now = datetime.now(timezone.utc) - start_time
    if now.seconds > 3000:
        print("Ending: continue from ID=%s" % user.id)
        sys.exit()
    user_profile = get_profile(user)
    if user_profile.last_read_access < limit:
        d = datetime.today() - user_profile.last_read_access
        print(user + " " * (20 - len(user.username)) + " %s days inactive" % d.days)
print("Execution summary")
print("%s total users" % len(users))
i = User.objects.filter(is_active__exact=0).count()
print("%s inactive users" % i)

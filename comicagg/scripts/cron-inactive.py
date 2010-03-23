#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, time
from datetime import datetime, timedelta
sys.path.insert(0, os.path.abspath('..'))
import settings_local
sys.path.insert(0, settings_local.ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = "comicagg.settings"

from comicagg.agregator.models import *
from django.contrib.auth.models import User

starttime = datetime.now()
if len(sys.argv) > 1:
    uid = int(sys.argv[1])
    users = User.objects.order_by('id').filter(id__gte = uid).filter(is_active__exact=1)
else:
    users = User.objects.filter(is_active__exact=1)
limit = datetime.today() - timedelta(45)
for user in users:
    now = datetime.now()-starttime
    if now.seconds > 3000:
        print "FIN: comenzar de nuevo desde id=", user.id
        sys.exit()
    up = user.get_profile()
    if up.last_read_access < limit:
        #print "setting user", user, "as inactive"
        user.is_active = False
        user.save()
        #borrar sus unreads
        user.unreadcomic_set.delete()
print "Resumen usuarios"
print len(users), "usuarios en total"
i = User.objects.filter(is_active__exact=0).count()
print i, "usuarios inactivos"
    #time.sleep(0.2)

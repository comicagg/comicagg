#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Updates the strips in the comics
"""
import os
import sys
import threading
from traceback import print_exc
from builtins import range
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

from comicagg.scripts import is_running, not_running_anymore
is_running()

from django.core.mail import mail_managers
from comicagg.comics.check import check_comic
from comicagg.comics.models import Comic, NoMatchException

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
                print('*** Interrupted %s ***' % datetime.now())
                sys.exit()
            except NoMatchException:
                s = '   Error checking %s\n' % comic.name
                if comic.activo:
                    self.errors_active.append(s)
                else:
                    self.errors_inactive.append(s)
                errors += 1
            except:
                s = '   Unexpected error %s: %s\n' % (comic.name, sys.exc_info()[1])
                if comic.activo:
                    self.errors_unexpected.append(s)
                else:
                    self.errors_inactive.append(s)
                errors += 1
            if changed:
                new += 1
                if not comic.activo or comic.ended:
                    s = '   Disabled or ended comic %s just got an update.\n' % comic.name
                    self.inactive_updated.append(s)
                else:
                    s = '   Updated %s\n' % comic.name
                    updated_comics.append(s)
            else:
                no_change += 1
            comic = self.next()

    def next(self):
        print("%s: %d left, %d errors" % (self.getName(), len(self.all), errors))
        if len(self.all):
            return self.all.pop(0)

print('\n*** Update job execution (%s) ***' % datetime.now())

execution_log = "Start time: %s\n" % datetime.now()
thread_list = list()
# Limit the number of threads to 5 or less if there are less comics in the service
max_threads = 5 if len(all) > 5 else len(all)
for i in range(max_threads):
    thread = CheckThread(all, errors_active, errors_inactive)
    thread_list.append(thread)
    thread.start()

for thread in thread_list:
    thread.join()

execution_log += "Errors in active comics\n"
for s in errors_active:
    execution_log += s
execution_log += "-------------------------\n"
execution_log += "Unexpected errors in active comics\n"
for s in errors_unexpected:
    execution_log += s
execution_log += "-------------------------\n"
execution_log += "Disabled comic updated\n"
for s in inactive_updated:
    execution_log += s
execution_log += "-------------------------\n"
execution_log += "Errors in disabled comics\n"
for s in errors_inactive:
    execution_log += s
execution_log += "-------------------------\n"
execution_log += "Updated comics\n"
for s in updated_comics:
    execution_log += s
execution_log += "-------------------------\n"

execution_log += "%s new, %s unchanged, %s errors\n" % (new, no_change, (len(errors_active)+len(errors_inactive)+len(errors_unexpected)))
execution_log += "End time: %s\n" % datetime.now()

try:
    mail_managers('Update job', execution_log)
except:
    print("Got error sending email")
    print_exc()
    
print(execution_log)
not_running_anymore()

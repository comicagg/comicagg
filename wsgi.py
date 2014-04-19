#!/usr/bin/env python2.7
import os
import sys

paths = [
    os.path.dirname(os.path.abspath(__file__)), # this django project
    '/home/esu/projects/comicagg/django.git' # my local clone of django
]

for path in paths:
    if path not in sys.path:
        sys.path.insert(0, path)

from django.core.handlers.wsgi import WSGIHandler

os.environ['DJANGO_SETTINGS_MODULE'] = 'comicagg.settings'
application = WSGIHandler()


#!/usr/bin/env python3
import os
import sys

paths = [
#    os.path.dirname(os.path.abspath(__file__)), # this django project
#    '/home/esu/projects/comicagg/django.git' # my local clone of django
]

for path in paths:
    if path not in sys.path:
        sys.path.insert(0, path)

from django.core.wsgi import get_wsgi_application

os.environ['DJANGO_SETTINGS_MODULE'] = 'comicagg.settings'
application = get_wsgi_application()

#!/usr/bin/env python2.7
import os
import sys

sys.path = ['/home/esu/projects/comicagg/comicagg.git', '/home/esu/projects/comicagg/comicagg.git/comicagg', '/home/esu/projects/comicagg/django.git'] + sys.path

from django.core.handlers.wsgi import WSGIHandler

os.environ['DJANGO_SETTINGS_MODULE'] = 'comicagg.settings'
application = WSGIHandler()


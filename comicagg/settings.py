# -*- coding: utf-8 -*-
# Django settings for comicagg project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('esú', 'admin@comicagg.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = ''           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = ''             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'CET'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
#MEDIA_ROOT = '/home/esu/dev/django/comicagg/media'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
#MEDIA_URL = 'https://localhost/media_comicagg/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
#ADMIN_MEDIA_PREFIX = '/admin-media/'

# Used for password reset email, without trailing slash
#DOMAIN = 'http://192.168.0.3:8000'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '0zqsc45e!e*%zy(&gus5p4bj6^mdrt%7^y*fl*(o6rt1yp=)&#'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'comicagg.middleware.UserBasedExceptionMiddleware',
    'comicagg.middleware.MaintenanceMiddleware',
)

ROOT_URLCONF = 'comicagg.urls'

#THEME = 'blue_white'

#TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #'/home/esu/dev/django/comicagg/templates',
    #'/home/esu/dev/django/comicagg/templates/base',
    #'/home/esu/dev/django/comicagg/templates/%s' % THEME,
#)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'comicagg.agregator',
    'comicagg.accounts',
    'comicagg.blog',
    'comicagg.help',
    'comicagg.todo',
)

SITE_NAME = 'Comic Aggregator'

AUTH_PROFILE_MODULE = "accounts.userprofile"

TAG_CLOUD_NUMBER = 1

EMAIL_HOST = 'mail.proyectoanonimo.com'
EMAIL_HOST_USER = 'robot+comicagg.com'
EMAIL_HOST_PASSWORD = 'robot%%'

CACHE_BACKEND = 'db://cachet1'

from settings_local import *

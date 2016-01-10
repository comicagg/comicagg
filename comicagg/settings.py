# -*- coding: utf-8 -*-
# Django settings for comicagg project.

import os

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

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

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds the comicagg folder
ROOT = os.path.dirname(os.path.abspath(__file__)) + '/'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(ROOT, 'media')

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
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(ROOT, 'templates'),
)

STATICFILES_DIRS = (
    os.path.join(ROOT, 'static'),
)

FIXTURE_DIRS = (
    os.path.join(ROOT, 'test_fixtures'),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware', # Compress the output
    'django.middleware.common.CommonMiddleware', #
    'django.contrib.sessions.middleware.SessionMiddleware', # Django sessions
    'django.middleware.csrf.CsrfViewMiddleware', # Cross site request forgery protection
    'django.middleware.locale.LocaleMiddleware', # Change the locale

    # Authentication middleware
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Default authentication
    'comicagg.api.middleware.OAuth2Middleware', # OAuth2 authentication

    # Post authentication middleware
    'comicagg.middleware.UserProfileMiddleware', # Set up the user profile and user operations
    #'comicagg.middleware.UserBasedExceptionMiddleware',
    'comicagg.middleware.ActiveUserMiddleware', # Check if the user is active
    'comicagg.middleware.MaintenanceMiddleware', # Maintenance mode
    'django.contrib.messages.middleware.MessageMiddleware', # Django messages
    'django.contrib.admindocs.middleware.XViewMiddleware',
    'comicagg.api.middleware.AcceptHeaderProcessingMiddleware', # Processes the Accept header
    'comicagg.api.middleware.BodyProcessingMiddleware' # Process the body
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

ROOT_URLCONF = 'comicagg.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'comicagg.accounts',
    'comicagg.api',
    'comicagg.blog',
    'comicagg.comics',
    'comicagg.todo',
    'provider',
    'provider.oauth2',
)

SITE_NAME = 'Comic Aggregator'

TAG_CLOUD_NUMBER = 1

INACTIVE_DAYS = 30

EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

SESSION_COOKIE_NAME = 'comicagg_session'

USER_AGENT = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)'

"""
Logging levels

CRITICAL    50
ERROR       40
WARNING     30
INFO        20
DEBUG       10
NOTSET      0
"""

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(process)d %(name)s %(levelname)s %(message)s'
        },
    },
    'filters': {},
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'logging.NullHandler',
        },
        'console': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'file': {
            'level':'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            # The user that runs the django process will need to have permissions in this folder
            'filename': os.path.join('/var/log/comicagg', 'comicagg.log'),
            'when': 'midnight',
            'backupCount': 30,
            'encoding': 'utf-8',
            'delay': True,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'comicagg': {
            'handlers': ['console'],
            'level': 'WARNING'
        },
        'provider': {
            'handlers': ['console'],
            'level': 'WARNING'
        },
    }
}

from comicagg.settings_local import *

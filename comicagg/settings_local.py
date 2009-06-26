# -*- coding: utf-8 -*-
# Django settings for comicagg project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

MAINTENANCE = False

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = '/home/esu/dev/comicagg/comicagg.db'             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Absolute path to the directory that holds the comicagg folder
# Example: "/home/media/media.lawrence.com/"
ROOT = '/home/esu/dev/comicagg/'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '%scomicagg/media' % ROOT

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = 'http://localhost:8000/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = 'http://localhost/admin-media/'

#used for password reset email
DOMAIN = 'http://192.168.0.3:8000'

THEME = 'blue_white'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '%scomicagg/templates' % ROOT,
    '%scomicagg/templates/base' % ROOT,
    '%scomicagg/templates/%s' % (ROOT, THEME),
)


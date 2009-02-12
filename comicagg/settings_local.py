# -*- coding: utf-8 -*-
# Django settings for comicagg project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'comic_ak'             # Or path to database file if using sqlite3.
DATABASE_USER = 'comic_ak'             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
ROOT = '/home/esu/dev/comicagg'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/home/esu/dev/comicagg/comicagg/media'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = 'http://localhost/media_comic_ak/'

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
    '/home/esu/dev/comicagg/comicagg/templates',
    '/home/esu/dev/comicagg/comicagg/templates/base',
    '/home/esu/dev/comicagg/comicagg/templates/%s' % THEME,
)


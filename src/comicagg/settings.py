# Django settings for comicagg project.

import os

from comicagg.utils import Env
from django.core.management.commands.runserver import Command as runserver

# Change default Django runserver address and port
runserver.default_addr = "0.0.0.0"
runserver.default_port = 8000

# Absolute path to the directory that holds the comicagg folder
ROOT = os.path.dirname(os.path.abspath(__file__)) + "/"

django_env = Env()

DEBUG = django_env.int("DEBUG", 0)
TEMPLATE_DEBUG = DEBUG

# comicagg.middleware.MaintenanceMiddleware
# Only superusers can access the site, others will see a message
MAINTENANCE = django_env.int("MAINTENANCE", 0)

# Make this unique, and don't share it with anybody.
SECRET_KEY = django_env.get("SECRET_KEY")

# ################
# #              #
# #   Database   #
# #              #
# ################

DATABASES = {
    # psycopg2://user:password@server:5432/path
    "default": django_env.db("DATABASE")
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# The lifetime of a database connection, as an integer of seconds.
# Use 0 to close database connections at the end of each request
# — Django’s historical behavior — and None for unlimited persistent database connections.
CONN_MAX_AGE = 1

# If set to True, existing persistent database connections will be health checked
# before they are reused in each request performing database access.
CONN_HEALTH_CHECKS = True

# List of directories searched for fixture files,
# in addition to the fixtures directory of each application, in search order.
FIXTURE_DIRS = (os.path.join(ROOT, "test_fixtures"),)

# ##############
# #            #
# #   Server   #
# #            #
# ##############

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "celery",
    "django_celery_beat",
    "django_celery_results",
    # Instead of 'django.contrib.admin'
    "comicagg.apps.ComicaggAdminConfig",
    "comicagg.accounts",
    # "comicagg.api",
    "comicagg.blog",
    "comicagg.comics",
    # "provider",
    # "provider.oauth2",
    "mailer",
]

MIDDLEWARE = [
    # ##########################
    # #   Pre-authentication   #
    # ##########################
    # https://docs.djangoproject.com/en/4.2/ref/middleware/#module-django.middleware.security
    "django.middleware.security.SecurityMiddleware",
    # https://docs.djangoproject.com/en/4.2/ref/middleware/#module-django.middleware.gzip
    "django.middleware.gzip.GZipMiddleware",
    # https://docs.djangoproject.com/en/4.2/topics/http/sessions/
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Enables language selection based on data from the request.
    "django.middleware.locale.LocaleMiddleware",
    # https://docs.djangoproject.com/en/4.2/ref/middleware/#module-django.middleware.common
    "django.middleware.common.CommonMiddleware",
    # https://docs.djangoproject.com/en/4.2/ref/csrf/
    "django.middleware.csrf.CsrfViewMiddleware",
    # ######################
    # #   Authentication   #
    # ######################
    # Adds the user attribute, representing the currently-logged-in user, to every incoming HttpRequest object.
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Overwrite the user object with our own User proxy model
    "comicagg.middleware.UserProxyOverwriteMiddleware",
    # OAuth2 authentication
    # "comicagg.api.middleware.OAuth2Middleware",
    # ###########################
    # #   Post-authentication   #
    # ###########################
    # Show detailed error pages to super users.
    #'comicagg.middleware.UserBasedExceptionMiddleware',
    # Set up the user profile and user operations
    # "comicagg.middleware.UserProfileMiddleware",
    # Check if the user is active
    "comicagg.middleware.ActiveUserMiddleware",
    # Maintenance mode
    "comicagg.middleware.MaintenanceMiddleware",
    # Django messages
    "django.contrib.messages.middleware.MessageMiddleware",
    # Clickjacking Protection
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "comicagg.urls"

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# A list of strings representing the host/domain names that this Django site can serve.
ALLOWED_HOSTS = django_env.list("ALLOWED_HOSTS")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(ROOT, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "comicagg.comics.context_processors.comic_counters",
                "django.template.context_processors.static",
                "comicagg.common.context_processors.add_settings",
            ],
        },
    },
]

# ######################
# #   Authentication   #
# ######################

SESSION_COOKIE_NAME = "comicagg_session"

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.AllowAllUsersModelBackend"]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
    # SHA1 was deprecated but it's needed for password auto-migration
    "django.contrib.auth.hashers.SHA1PasswordHasher",
]

# CSRF_TRUSTED_ORIGINS = []

# CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

# ######################
# #                    #
# #   URLs and paths   #
# #                    #
# ######################

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
# MEDIA_ROOT = os.path.join(ROOT, "media")
MEDIA_ROOT = django_env.get("MEDIA_ROOT")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
# MEDIA_URL = 'https://localhost/media_comicagg/'
MEDIA_URL = django_env.get("MEDIA_URL")

# The absolute path to the directory where collectstatic will collect static files for deployment.
STATIC_ROOT = django_env.get("STATIC_ROOT")

# URL to use when referring to static files located in STATIC_ROOT.
STATIC_URL = django_env.get("STATIC_URL")

# This setting defines the additional locations the staticfiles app will traverse if the FileSystemFinder finder is enabled
# This should be set to a list of strings that contain full paths to your additional files directory(ies)
STATICFILES_DIRS = (os.path.join(ROOT, "static"),)

# ######################################
# #                                    #
# #   Dates and internationalization   #
# #                                    #
# ######################################

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "UTC"
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en"

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# The ID, as an integer, of the current site in the django_site database table.
# This is used so that application data can hook into specific sites
# and a single database can manage content for multiple sites.
SITE_ID = 1

# #############
# #           #
# #   Email   #
# #           #
# #############

# The backend to use for sending emails.
EMAIL_BACKEND = "mailer.backend.DbBackend"

# A list of all the people who get code error notifications.
# When DEBUG=False and AdminEmailHandler is configured in LOGGING (done by default),
# Django emails these people the details of exceptions raised in the request/response cycle.
ADMINS = django_env.email_list("ADMINS")

# A list in the same format as ADMINS that specifies who should get broken link notifications
# when BrokenLinkEmailsMiddleware is enabled.
MANAGERS = django_env.email_list("MANAGERS")

# Expected value: //user:password@host:port
email = django_env.url("EMAIL_HOST")
EMAIL_HOST = email.hostname
EMAIL_HOST_USER = email.username
EMAIL_HOST_PASSWORD = email.password
EMAIL_PORT = email.port

# Default email address to use for various automated correspondence from the site manager(s).
# This doesn’t include error messages sent to ADMINS and MANAGERS
DEFAULT_FROM_EMAIL = django_env.get("DEFAULT_FROM_EMAIL")

# The email address that error messages come from, such as those sent to ADMINS and MANAGERS.
# This address is used only for error messages.
SERVER_EMAIL = django_env.get("SERVER_EMAIL")

# Subject-line prefix for email messages sent with django.core.mail.mail_admins
# or django.core.mail.mail_managers. You’ll probably want to include the trailing space.
EMAIL_SUBJECT_PREFIX = "[Comicagg] "

# ###############
# #             #
# #   Logging   #
# #             #
# ###############

"""
Logging levels

CRITICAL    50
ERROR       40
WARNING     30
INFO        20
DEBUG       10
NOTSET      0
"""

LOGS_DIR = django_env.get("LOGS_DIR")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(process)d %(name)s %(levelname)s %(message)s"
        },
    },
    "filters": {},
    "handlers": {
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            # The user that runs the django process will need to have permissions in this folder
            "filename": os.path.join(LOGS_DIR, "comicagg.log"),
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf-8",
            "delay": True,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console", "mail_admins"],
            "level": "INFO",
            "propagate": False,
        },
        "comicagg": {"handlers": ["console"], "level": "WARNING"},
        "provider": {"handlers": ["console"], "level": "WARNING"},
        "mailer": {"level": "INFO", "propagate": True},
    },
}

# ##############
# #            #
# #   Custom   #
# #            #
# ##############

SITE_NAME = "Comic Aggregator"

# Without trailing slash, used in the password reset email and ws index page
SITE_DOMAIN = django_env.get("SITE_DOMAIN")

INACTIVE_DAYS = 60
MAX_UNREADS_PER_USER = 20

# #################
# #               #
# #   Scrapping   #
# #               #
# #################

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.46"

# ####################
# #                  #
# #   Celery tasks   #
# #                  #
# ####################

celery_env = Env("CELERY")
CELERY_BROKER_URL = celery_env.get("BROKER_URL")  # "redis://redis:6379"
CELERY_RESULT_BACKEND = "django-db"  # "redis://redis:6379"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # seconds
CELERY_RESULT_EXTENDED = True

# ############################
# #   django-debug-toolbar   #
# ############################
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]

    MIDDLEWARE.insert(2, "debug_toolbar.middleware.DebugToolbarMiddleware")

    import socket  # only if you haven't already imported this

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
        "127.0.0.1",
        "10.0.2.2",
    ]

    # https://timonweb.com/django/fixing-the-data-for-this-panel-isnt-available-anymore-error-in-django-debug-toolbar/
    RESULTS_CACHE_SIZE = 1000
    hide_toolbar_patterns = ["/media/", "/static/", "/comics/strip/"]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: not any(
            request.path.startswith(p) for p in hide_toolbar_patterns
        ),
    }

from django.http import HttpRequest
from django.conf import settings


def comicagg_vars(request: HttpRequest):
    return {
        "MAINTENANCE": settings.MAINTENANCE,
        "DATABASE_NAME": settings.DATABASES["default"]["NAME"],
        "INACTIVE_DAYS": settings.INACTIVE_DAYS,
        "SITE_DOMAIN": settings.SITE_DOMAIN,
    }

from django.http import HttpRequest
from django.conf import settings


def add_settings(request: HttpRequest):
    """Add some properties from settings to the context."""
    return {
        "MAINTENANCE": settings.MAINTENANCE,
        "DATABASE_NAME": settings.DATABASES["default"]["NAME"],
        "INACTIVE_DAYS": settings.INACTIVE_DAYS,
        "SITE_DOMAIN": settings.SITE_DOMAIN,
    }

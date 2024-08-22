from django.http import HttpRequest
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site


def add_settings(request: HttpRequest):
    """Add additional properties to the context."""
    return {
        "MAINTENANCE": settings.MAINTENANCE,
        "DATABASE_NAME": settings.DATABASES["default"]["NAME"],
        "INACTIVE_DAYS": settings.INACTIVE_DAYS,
        "CODE_REPO": settings.CODE_REPO,
        "SITE_DOMAIN": get_current_site(request).domain,
        "SITE_NAME": get_current_site(request).name,
    }

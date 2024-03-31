from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from .views import welcome, robots

urlpatterns = [
    path("", welcome, name="index"),
    path("accounts/", include("accounts.urls")),
    path("comics/", include("comics.urls")),
    path("news/", include("blog.urls")),
    path("ws/", include("ws.urls")),
    path("about/", include("about.urls")),
    # path("api/", include("comicagg.api.urls")),
    # path("oauth2/", include("provider.oauth2.urls", namespace="oauth2")),
    path("robots.txt", robots, name="robots"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    # Serve files from MEDIA_ROOT if Debug
    from django.views.static import serve

    serve_config = {
        "document_root": settings.MEDIA_ROOT,
    }

    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, serve_config),
        path("__debug__/", include("debug_toolbar.urls")),
    ]

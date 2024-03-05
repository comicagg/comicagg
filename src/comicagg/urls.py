from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import TemplateView

from comicagg.views import welcome

robots_txt = TemplateView.as_view(template_name="robots.txt", content_type="text/plain")

urlpatterns = [
    path("", welcome, name="index"),
    path("accounts/", include("comicagg.accounts.urls")),
    path("comics/", include("comicagg.comics.urls")),
    path("news/", include("comicagg.blog.urls")),
    path("ws/", include("comicagg.ws.urls")),
    path("about/", include("comicagg.about.urls")),
    # path("api/", include("comicagg.api.urls")),
    # path("oauth2/", include("provider.oauth2.urls", namespace="oauth2")),
    path("robots.txt", robots_txt, name="robots"),
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

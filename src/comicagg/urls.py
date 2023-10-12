# -*- coding: utf-8 -*-
# from django.conf.urls import patterns, url, include
from django.contrib import admin
# from comicagg.admin import admin_site
from django.urls import include, path

from comicagg.accounts import views as accounts_views
from comicagg import robots_txt
from comicagg.common.views import BaseTemplateView
from comicagg.comics import views as comics_views

# admin.autodiscover()

handler404 = "comicagg.error404"
handler500 = "comicagg.error500"

urlpatterns = [
    path("", accounts_views.index, name="index"),
    path("robots.txt", robots_txt, name="robots"),

    path("admin/", admin.site.urls),

    path("stats/", comics_views.stats, name="stats"),
    path("accounts/", include("comicagg.accounts.urls", namespace="accounts")),
    path("api/", include("comicagg.api.urls", namespace="api")),
    path("comics/", include("comicagg.comics.urls", namespace="comics")),
    path("news/", include("comicagg.blog.urls", namespace="news")),

    path("oauth2/", include("provider.oauth2.urls", namespace="oauth2")),
    path("ws/", include("comicagg.ws.urls")),

    path(
        "docs/custom_func/",
        BaseTemplateView.as_view(template_name="admin/custom_func.html"),
        name="docs_custom",
    ),
    path(
        "contact/",
        BaseTemplateView.as_view(template_name="contact.html"),
        name="contact",
    ),
]

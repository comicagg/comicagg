# -*- coding: utf-8 -*-
from django.contrib import admin
from django.urls import include, path

from comicagg.accounts import views as accounts_views
from comicagg import robots_txt
from comicagg.common.views import BaseTemplateView
from comicagg.comics import views as comics_views

handler404 = "comicagg.error404"
handler500 = "comicagg.error500"

urlpatterns = [
    path("", accounts_views.index, name="index"),
    path("robots.txt", robots_txt, name="robots"),

    path("admin/", admin.site.urls),

    path("stats/", comics_views.stats, name="stats"),
    path("accounts/", include("comicagg.accounts.urls")),
    path("api/", include("comicagg.api.urls")),
    path("comics/", include("comicagg.comics.urls")),
    path("news/", include("comicagg.blog.urls")),

    path("oauth2/", include("provider.oauth2.urls", namespace="oauth2")),
    path("ws/", include("comicagg.ws.urls")),

    path(
        "docs/custom_func/",
        admin.site.admin_view(BaseTemplateView.as_view(template_name="admin/custom_func.html")),
        name="docs_custom",
    ),
    path(
        "contact/",
        BaseTemplateView.as_view(template_name="contact.html"),
        name="contact",
    ),
]

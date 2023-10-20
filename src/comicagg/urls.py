# -*- coding: utf-8 -*-
from django.contrib import admin
from django.urls import include, path

from comicagg.accounts import views as accounts_views
from comicagg.views import robots_txt
from comicagg.common.views import BaseTemplateView
from comicagg.comics import views as comics_views

urlpatterns = [
    path("", accounts_views.index, name="index"),
    path("accounts/", include("comicagg.accounts.urls")),
    path("comics/", include("comicagg.comics.urls")),
    path("news/", include("comicagg.blog.urls")),
    path("ws/", include("comicagg.ws.urls")),
    path("api/", include("comicagg.api.urls")),
    path("oauth2/", include("provider.oauth2.urls", namespace="oauth2")),
    path("stats/", comics_views.stats, name="stats"),
    path("robots.txt", robots_txt, name="robots"),
    path(
        "docs/custom_func/",
        admin.site.admin_view(
            BaseTemplateView.as_view(template_name="admin/custom_func.html")
        ),
        name="docs_custom",
    ),
    path(
        "contact/",
        BaseTemplateView.as_view(template_name="contact.html"),
        name="contact",
    ),
    path("admin/", admin.site.urls),
]
# -*- coding: utf-8 -*-
from django.urls import include, path, re_path

from . import views

app_name = "comics"
urlpatterns = [
    path("", views.read_view, name="index"),
    path("read/", views.read_view, name="read"),
    path("add/", views.organize, {"add": True}, name="add"),
    path("organize/", views.organize, name="organize"),
    path("request/", views.request_index, name="requests"),

    re_path(r"^li/(?P<cid>\d+)/", views.last_image_url, name="last_image_url"),
    re_path(r"^hi/(?P<hid>\d+)/", views.history_image_url, name="history_url"),

    path("ajax/", include("comicagg.comics.ajax.urls", namespace="ajax")),
]

# -*- coding: utf-8 -*-
from django.urls import include, path
from . import views

ajax_patterns = (
    [
        path("ajax/forget_news/", views.forget_new_blogs, name="forget_new_blogs")
    ],
    "ajax",
)

app_name = "news"
urlpatterns = [
    path("", views.index, name="index"),
    path("all/", views.index, name="archive", kwargs={"archive": True}),
    path("ajax/", include(ajax_patterns)),
]

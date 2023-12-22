from django.urls import include, path, re_path

from . import views

app_name = "comics"
urlpatterns = [
    path("", views.read_view, name="index"),
    path("read/", views.read_view, name="read"),
    path("add/", views.add_comics, name="add"),
    path("organize/", views.organize, name="organize"),
    path("request/", views.request_index, name="requests"),

    re_path(r"^li/(?P<comic_id>\d+)/", views.last_image_url, name="last_image_url"),
    re_path(r"^strip/(?P<strip_id>\d+)/", views.strip_image_url, name="strip_url"),

    path("stats/",views.stats, name="stats"),

    path("ajax/", include("comicagg.comics.ajax.urls", namespace="ajax")),
]

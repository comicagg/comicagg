from django.urls import path, re_path

from . import views

app_name = "admin"
urlpatterns = [
    path("update/", views.admin_update_view, name="update_comics"),
    re_path(
        r"^update/(?P<comic_id>\d+)/$",
        views.admin_update_view,
        name="update_comic",
    ),
    re_path(r"^reported/(?P<chids>[\w-]+)/$", views.admin_reported, name="reported"),
]

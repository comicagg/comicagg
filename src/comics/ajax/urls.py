from django.urls import path, re_path

from . import views

app_name = "ajax"
urlpatterns = [
    re_path(r"x/comic/(?P<comic_id>\d+)/", views.x_comic, name="x_comic"),
    re_path(r"x/add/(?P<comic_id>\d+)/", views.x_comic, name="x_add", kwargs={"add": True}),
    re_path(r"x/remove/(?P<comic_id>\d+)/", views.x_comic, name="x_remove", kwargs={"remove": True}),
    path("add_comic/", views.add_comic, name="add_comic"),
    path("remove_comic/", views.remove_comic, name="remove_comic"),
    path("remove_comic_list/", views.remove_comic_list, name="remove_comic_list"),
    path("report_comic/", views.report_comic, name="report_comic"),
    path("organize/forget/", views.forget_new_comic, name="forget_new_comic"),
    path("organize/save/", views.save_selection, name="save"),
    path("mark_read/", views.mark_read, name="mark_read"),
    path("mark_all_read/", views.mark_all_read, name="mark_all_read"),
]

from django.urls import path

from . import views

app_name = "ajax"
urlpatterns = [
    path("add_comic/", views.add_comic, name="add_comic"),
    path("remove_comic/", views.remove_comic, name="remove_comic"),
    path("remove_comic_list/", views.remove_comic_list, name="remove_comic_list"),
    path("report_comic/", views.report_comic, name="report_comic"),
    path("organize/forget/", views.forget_new_comic, name="forget_new_comic"),
    path("organize/save/", views.save_selection, name="save"),
    path("mark_read/", views.mark_read, name="mark_read"),
    path("mark_all_read/", views.mark_all_read, name="mark_all_read"),
]

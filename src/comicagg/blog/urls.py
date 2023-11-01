from django.urls import include, path

from . import views

app_name = "news"

ajax_patterns = (
    [path("forget_news/", views.forget_new_blogs, name="forget_new_blogs")],
    "ajax",
)

urlpatterns = [
    path("", views.index, name="index"),
    path("all/", views.index, name="archive", kwargs={"all": True}),
    path("ajax/", include(ajax_patterns)),
]

from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt
from comicagg.api.views import (
    IndexView,
    ComicsView,
    StripsView,
    SubscriptionsView,
    UnreadsView,
    UserView,
)

app_name = "comics"
urlpatterns = [
    path(r"^$", IndexView.as_view(), name="index"),
    path(r"^comics$", ComicsView.as_view(), name="comics"),
    re_path(r"^comics/(?P<comic_id>\d+)$", ComicsView.as_view(), name="comic_info"),
    path(
        r"^subscriptions$",
        csrf_exempt(SubscriptionsView.as_view()),
        name="subscriptions",
    ),
    path(r"^unreads$", UnreadsView.as_view(), name="unreads"),
    re_path(
        r"^unreads/(?P<comic_id>\d+)$",
        csrf_exempt(UnreadsView.as_view()),
        name="unreads_comic",
    ),
    re_path(
        r"^strips/(?P<strip_id>\d+)$",
        csrf_exempt(StripsView.as_view()),
        name="strip_info",
    ),
    path(r"^user$", UserView.as_view(), name="user_info"),
]

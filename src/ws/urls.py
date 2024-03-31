from django.urls import path, re_path

from . import views

app_name = "ws"
urlpatterns = [
    path("", views.index, name="index"),
    re_path(r"^(?P<user>.*)/unread$", views.unread_user, name="unread_user"),
    path(
        "subscriptionssimple/",
        views.user_subscriptions,
        {"simple": True},
        name="user_subscriptions_simple",
    ),
    path("subscriptions/", views.user_subscriptions, name="user_subscriptions"),
]

# -*- coding: utf-8 -*-
from django.urls import path, re_path
from . import views

app_name = "accounts"
urlpatterns = [
    path("profile/", views.view_profile, name="profile"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("password/change/", views.password_change, name="password_change"),
    path("password/reset/", views.password_reset, name="password_reset"),
    path("email/", views.update_email, name="email_change"),
    re_path(r"done_(?P<kind>\w+)/", views.done, name="done"),
    path("activate/", views.activate, name="activate"),
]

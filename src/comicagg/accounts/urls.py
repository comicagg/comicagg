# -*- coding: utf-8 -*-
from django.urls import path, re_path
from . import views

app_name = "accounts"
urlpatterns = [
    path("profile/", views.edit_profile, name="profile"),
    # path('profile/saved/', 'edit_profile', name='saved_profile', kwargs={'saved':True}),
    # path('profile/save/', 'save_profile', name='save_profile'),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("password/change/", views.password_change, name="password_change"),
    path("password/reset/", views.password_reset, name="password_reset"),
    path("email/", views.email, name="email_change"),
    re_path("done_(?P<kind>\w+)/", views.done, name="done"),
    path("activate/", views.activate, name="activate"),
]

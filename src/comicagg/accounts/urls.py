from django.urls import path, re_path

from . import views

app_name = "accounts"
urlpatterns = [
    path("profile/", views.view_profile, name="profile"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path(
        "password/change/", views.PasswordChangeView.as_view(), name="password_change"
    ),
    path("email/", views.UpdateEmail.as_view(), name="email_change"),
    path("activate/", views.activate, name="activate"),
    path("delete_account/", views.DeleteAccount.as_view(), name="delete_account"),
    re_path(r"done_(?P<kind>\w+)/", views.done, name="done"),
] + [
    path("password/reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password/reset/done/",
        views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]

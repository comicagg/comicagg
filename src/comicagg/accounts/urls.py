from django.urls import path, re_path

from . import views

app_name = "accounts"
urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("password/change/", views.PasswordChangeView.as_view(), name="password_change"),
    path("password/change/done/", views.PasswordChangeDoneView.as_view(), name="password_change_done"),
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
    path("email/", views.UpdateEmailView.as_view(), name="email_change"),
    path("email/done/", views.UpdateEmailDoneView.as_view(), name="email_change_done"),
    path("activate/", views.ActivateView.as_view(), name="activate"),
    path("delete/", views.DeleteAccountView.as_view(), name="delete_account"),
    path("delete/done/", views.DeleteAccountDoneView.as_view(), name="delete_account_done"),
]

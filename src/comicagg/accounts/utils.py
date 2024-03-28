from django.http import HttpRequest
from django.utils.translation import gettext as _

from comicagg.accounts.models import UserProfile
from comicagg.utils import send_email


def get_profile(user):
    return UserProfile.objects.get(user=user)


def send_password_updated_email(request: HttpRequest, to_email: str):
    subject = _("Password updated")
    send_email(request, to_email, subject, "accounts/email_change_email.html")


def send_account_created_email(request: HttpRequest, to_email: str, username: str):
    subject = _("Account created")
    context = {"username": username}
    send_email(request, to_email, subject, "accounts/register_email.html", context)


def send_account_deleted_email(request: HttpRequest, to_email: str):
    subject = _("Account deleted")
    send_email(request, to_email, subject, "accounts/delete_account_email.html")

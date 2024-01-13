from celery import current_app
from django.http import HttpRequest

from comicagg.accounts.models import User


class AuthenticatedHttpRequest(HttpRequest):
    user: User
    current_app: str

from django.http import HttpRequest

from comicagg.accounts.models import User


class AuthenticatedHttpRequest(HttpRequest):
    user: User

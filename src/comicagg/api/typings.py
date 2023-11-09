from django.contrib.auth.models import User
from django.http import HttpRequest
from provider.oauth2.models import AccessToken


class OAuth2HttpRequest(HttpRequest):
    access_token: AccessToken | None
    scope: int
    session: dict | None
    user: User

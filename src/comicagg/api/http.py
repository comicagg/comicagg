from django.http import HttpRequest, HttpResponse

from provider.oauth2.models import AccessToken

from comicagg.accounts.models import User


class OAuth2HttpRequest(HttpRequest):
    access_token: AccessToken | None
    scope: int
    session: dict | None
    user: User


# ########################################
# #   Additional HTTP Response classes   #
# ########################################


class HttpResponseUnauthorized(HttpResponse):
    status_code = 401


class HttpResponseCreated(HttpResponse):
    status_code = 201


class HttpResponseNoContent(HttpResponse):
    status_code = 204

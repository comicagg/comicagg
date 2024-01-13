import logging
from datetime import timedelta

from django.urls import reverse

from .. import constants
from ..utils import now
from ..views import AccessToken as AccessTokenView
from ..views import Authorize, Capture, OAuthError, Redirect
from .backends import (
    BasicClientBackend,
    PublicPasswordBackend,
    RequestParamsClientBackend,
)
from .forms import (
    AuthorizationCodeGrantForm,
    AuthorizationForm,
    AuthorizationRequestForm,
    PasswordGrantForm,
    RefreshTokenGrantForm,
)
from .models import AccessToken, Client, RefreshToken

logger = logging.getLogger(__name__)


class Capture(Capture):
    """
    Implementation of :class:`provider.views.Capture`.
    """

    def get_redirect_url(self, request):
        return reverse("oauth2:authorize")


class Authorize(Authorize):
    """
    Implementation of :class:`provider.views.Authorize`.
    """

    def get_request_form(self, client, data):
        return AuthorizationRequestForm(data, client=client)

    def get_authorization_form(self, request, client, data, client_data):
        return AuthorizationForm(data)

    def get_client(self, client_id):
        try:
            return Client.objects.get(client_id=client_id)
        except Client.DoesNotExist:
            return None

    def get_redirect_url(self, request):
        return reverse("oauth2:redirect")

    def save_authorization(self, request, client, form, client_data):
        grant = form.save(commit=False)

        if grant is None:
            return None

        grant.user = request.user
        grant.client = client
        grant.redirect_uri = client_data.get("redirect_uri", "")
        grant.save()
        return grant.code


class Redirect(Redirect):
    """
    Implementation of :class:`provider.views.Redirect`
    """

    pass


class AccessTokenView(AccessTokenView):
    """
    Implementation of :class:`provider.views.AccessToken`.

    .. note:: This implementation does provide all default grant types defined
        in :attr:`provider.views.AccessToken.grant_types`. If you
        wish to disable any, you can override the :meth:`get_handler` method
        *or* the :attr:`grant_types` list.
    """

    authentication = (
        BasicClientBackend,
        RequestParamsClientBackend,
        PublicPasswordBackend,
    )

    def get_authorization_code_grant(self, request, data, client):
        logger.debug("AccessTokenView.get_authorization_code_grant enter")
        form = AuthorizationCodeGrantForm(data, client=client)
        if not form.is_valid():
            logger.error(
                "AccessTokenView.get_authorization_code_grant Form is not valid"
            )
            raise OAuthError(form.errors)
        return form.cleaned_data.get("grant")

    def get_refresh_token_grant(self, request, data, client):
        logger.debug("AccessTokenView.get_refresh_token_grant enter")
        form = RefreshTokenGrantForm(data, client=client)
        if not form.is_valid():
            raise OAuthError(form.errors)
        return form.cleaned_data.get("refresh_token")

    def get_password_grant(self, request, data, client):
        logger.debug("AccessTokenView.get_password_grant enter")
        form = PasswordGrantForm(data, client=client)
        if not form.is_valid():
            raise OAuthError(form.errors)
        return form.cleaned_data

    def get_access_token(self, request, user, scope, client):
        logger.debug("AccessTokenView.get_access_token enter")
        try:
            # Attempt to fetch an existing access token.
            at = AccessToken.objects.get(
                user=user, client=client, scope=scope, expires__gt=now()
            )
        except AccessToken.DoesNotExist:
            # None found... make a new one!
            at = self.create_access_token(request, user, scope, client)
            self.create_refresh_token(request, user, scope, at, client)
        return at

    def create_access_token(self, request, user, scope, client):
        logger.debug("AccessTokenView.create_access_token enter")
        return AccessToken.objects.create(user=user, client=client, scope=scope)

    def create_refresh_token(self, request, user, scope, access_token, client):
        logger.debug("AccessTokenView.create_refresh_token enter")
        return RefreshToken.objects.create(
            user=user, access_token=access_token, client=client
        )

    def invalidate_grant(self, grant):
        if constants.DELETE_EXPIRED:
            grant.delete()
        else:
            grant.expires = now() - timedelta(days=1)
            grant.save()

    def invalidate_refresh_token(self, rt):
        if constants.DELETE_EXPIRED:
            rt.delete()
        else:
            rt.expired = True
            rt.save()

    def invalidate_access_token(self, at):
        if constants.DELETE_EXPIRED:
            at.delete()
        else:
            at.expires = now() - timedelta(days=1)
            at.save()

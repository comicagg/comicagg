from django.db import models
from ..utils import now

class AccessTokenManager(models.Manager):
    def get_token(self, token):
        return self.get(token=token, expires__gt=now())

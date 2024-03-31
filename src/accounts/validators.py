import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

def validate_captcha(value: str):
    if value != "comic":
        raise ValidationError(_("Wrong word!"))


def validate_username(value: str):
    if re.compile(r"[^a-zA-Z0-9_.]").search(value):
        raise ValidationError(_("Some letters are not valid."))


def validate_user_exists(value: str):
    if User.objects.filter(username=value).count():
        raise ValidationError(
            _("That username is not valid, sorry. Please choose another.")
        )

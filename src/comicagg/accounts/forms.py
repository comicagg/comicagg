from typing import Tuple
from django import forms
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .validators import *


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    oauth2 = forms.BooleanField(widget=forms.HiddenInput(), required=False)


class EmailChangeForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"size": "25", "autocomplete": "new-password"})
    )
    email = forms.EmailField(widget=forms.TextInput(attrs={"size": "35", "autocomplete": "email"}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]
        if password and not self.user.check_password(password):
            raise ValidationError(_("Password is invalid!"))

    def save(self) -> Tuple[str, str]:
        new_email = self.cleaned_data["email"]
        old_email = self.user.email
        self.user.email = new_email
        self.user.save()
        return (old_email, new_email)


class PasswordResetForm(DjangoPasswordResetForm):
    def get_users(self, email_or_username):
        # Check if there are valid email add
        users_email = list(User.objects.filter(email__iexact=email_or_username))
        # Check if there is a username
        users_username = list(User.objects.filter(username__iexact=email_or_username))
        return users_email + users_username


class RegisterForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30"}),
        validators=[validate_username, validate_user_exists],
    )
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={"size": "25"}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={"size": "25"}))
    email = forms.EmailField(widget=forms.TextInput(attrs={"size": "50"}))
    captcha = forms.CharField(widget=forms.TextInput(attrs={"size": "10"}), validators=[validate_captcha])

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 != password2:
            raise ValidationError(_("Passwords don't match!"))


class DeleteAccountForm(forms.Form):
    confirmation = forms.BooleanField(label=_("Yes, I want to delete my account"), required=False)

    def clean_confirmation(self):
        confirmation = self.cleaned_data["confirmation"]
        if not confirmation:
            raise ValidationError(_("Please, confirm that you want to delete your account"))

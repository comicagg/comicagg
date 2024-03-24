from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import PasswordResetForm

from .validators import *


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    oauth2 = forms.BooleanField(widget=forms.HiddenInput(), required=False)


class EmailChangeForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"size": "25"}))
    email = forms.EmailField(widget=forms.TextInput(attrs={"size": "35"}))


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={"size": "25"}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={"size": "25"}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={"size": "25"}))


class PasswordResetForm(PasswordResetForm):
    email = forms.CharField(widget=forms.TextInput(attrs={"size": "35"}))

    def get_users(self, email_or_username):
        # Check if there are valid email add
        users_email = list(User.objects.filter(email__iexact=email_or_username))
        # Check if there is a username
        users_username = list(
            User.objects.filter(username__iexact=email_or_username)
        )
        return users_email + users_username

class RegisterForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"size": "30"}),
        validators=[validate_username, validate_user_exists],
    )
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={"size": "25"}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={"size": "25"}))
    email = forms.EmailField(widget=forms.TextInput(attrs={"size": "50"}))
    captcha = forms.CharField(
        widget=forms.TextInput(attrs={"size": "10"}), validators=[validate_captcha]
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 != password2:
            raise ValidationError(_("Passwords don't match!"))


class DeleteAccountForm(forms.Form):
    confirmation = forms.BooleanField(
        label=_("Yes, I want to delete my account"), required=False
    )

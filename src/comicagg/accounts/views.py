from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views import View

from comicagg.about.utils import ConsentRequiredMixin, consent_required, consent_show
from comicagg.typings import AuthenticatedHttpRequest

from .forms import (
    DeleteAccountForm,
    EmailChangeForm,
    LoginForm,
    PasswordChangeForm,
    PasswordResetForm,
    RegisterForm,
)


def done(request: HttpRequest, kind: str):
    try:
        return render(request, f"accounts/{kind}_done.html", {})
    except Exception:
        print(f"Error rendering {kind}_done.html")
        return redirect("index")


def logout_view(request: HttpRequest):
    logout(request)
    return redirect("index")


@consent_required
@login_required
def activate(request: AuthenticatedHttpRequest):
    if request.method == "POST":
        request.user.is_active = True
        request.user.save()
        return redirect("index")
    return render(request, "accounts/activate.html", {})


@consent_required
@login_required
def view_profile(request: AuthenticatedHttpRequest):
    return render(request, "accounts/account.html", {})


class LoginView(View):
    @consent_show
    def get(self, request: HttpRequest, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("index")
        context: dict[str, Any] = {"parent_template": "base.html"}
        next_url = request.GET["next"] if "next" in request.GET else ""
        form = LoginForm(initial={"next": next_url})
        if next_url.count("/oauth2/"):
            context["parent_template"] = "simple_base.html"
            context["oauth2"] = True
            form = LoginForm(initial={"next": next_url, "oauth2": True})
        context["form"] = form
        return render(request, "accounts/login_form.html", context)

    @consent_required
    def post(self, request: HttpRequest, *args, **kwargs):
        form = LoginForm(request.POST)
        if not form.is_valid():
            context = {"form": form}
            return render(request, "accounts/login_form.html", context, "login")
        # Form is valid, try authenticating the user
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        next_url = form.cleaned_data["next"]
        oauth2 = form.cleaned_data["oauth2"]
        if user := authenticate(request, username=username, password=password):
            # From now on the user is logged in
            login(request, user)
            if user.is_active:
                # Redirect to the page he was requesting.
                return (
                    HttpResponseRedirect(next_url)
                    if next_url
                    else redirect("comics:read")
                )
            # User was inactive, redirect to activate page
            return redirect("accounts:activate")
        # Return an 'invalid login' error message.
        form_initial = {"username": username, "next": next_url, "oauth2": oauth2}
        context: dict[str, Any] = {
            "parent_template": "simple_base.html" if oauth2 else "base.html",
            "error": _("Username or password not valid!"),
            "oauth2": oauth2,
            "form": LoginForm(initial=form_initial),
        }
        return render(request, "accounts/login_form.html", context)


class RegisterView(ConsentRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("index")
        logout(request)
        form = RegisterForm()
        context = {"form": form}
        return render(request, "accounts/register.html", context)

    def post(self, request: HttpRequest, *args, **kwargs):
        form = RegisterForm(request.POST)
        if not form.is_valid():
            context = {"form": form}
            return render(request, "accounts/register.html", context)
        username = form.cleaned_data["username"]
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password1"]
        User.objects.create_user(username, email, password)
        message_text = _(
            "Your account has been created. "
            "You can now log in using the username you selected."
        )
        messages.add_message(request, messages.SUCCESS, message_text)
        return redirect("accounts:login")


class PasswordResetView(ConsentRequiredMixin, PasswordResetView):
    subject_template_name = "accounts/password_reset_subject.html"
    email_template_name = "accounts/password_reset_email.html"
    # html_email_template_name = None
    template_name = "accounts/password_reset_form.html"
    form_class = PasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"

class PasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

class PasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"

class PasswordChangeView(ConsentRequiredMixin, LoginRequiredMixin, View):
    def get(self, request: AuthenticatedHttpRequest, *args, **kwargs):
        form = PasswordChangeForm()
        context = {"form": form}
        return render(request, "accounts/password_change_form.html", context)

    def post(self, request: AuthenticatedHttpRequest, *args, **kwargs):
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            old = form.cleaned_data["old_password"]
            new1 = form.cleaned_data["new_password1"]
            new2 = form.cleaned_data["new_password2"]
            if not request.user.check_password(old):
                form.errors["not_valid"] = True
            if new1 != new2:
                form.errors["are_different"] = True
            if not form.errors:
                request.user.set_password(new1)
                request.user.save()
                return redirect("accounts:done", kind="password_change")
        context = {"form": form}
        return render(request, "accounts/password_change_form.html", context)


class UpdateEmail(ConsentRequiredMixin, LoginRequiredMixin, View):
    def get(self, request: AuthenticatedHttpRequest, *args, **kwargs):
        form = EmailChangeForm()
        context = {"form": form}
        return render(request, "accounts/email_change_form.html", context)

    def post(self, request: AuthenticatedHttpRequest, *args, **kwargs):
        form = EmailChangeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            if not request.user.check_password(password):
                form.errors["incorrect_password"] = True
            else:
                request.user.email = email
                request.user.save()
                return redirect("accounts:done", kind="email_change")
        context = {"form": form}
        return render(request, "accounts/email_change_form.html", context)


class DeleteAccount(ConsentRequiredMixin, LoginRequiredMixin, View):
    def get(self, request: AuthenticatedHttpRequest, *args, **kwargs):
        form = DeleteAccountForm()
        context = {"form": form}
        return render(request, "accounts/delete_account_form.html", context)

    def post(self, request: AuthenticatedHttpRequest, *args, **kwargs):
        form = DeleteAccountForm(request.POST)
        if form.is_valid():
            confirmation = form.cleaned_data["confirmation"]
            if confirmation:
                user = User.objects.get(pk=request.user.pk)
                if user.is_superuser:
                    raise CannotDeleteSuperuserError()

                logout(request)
                user.delete()
                return redirect("accounts:done", kind="delete_account")
            form.errors["confirmation"] = True
        context = {"form": form}
        return render(request, "accounts/delete_account_form.html", context)


class CannotDeleteSuperuserError(Exception):
    pass

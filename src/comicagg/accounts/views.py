from typing import Any, cast

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeDoneView as DjPasswordChangeDoneView
from django.contrib.auth.views import PasswordChangeView as DjPasswordChangeView
from django.contrib.auth.views import PasswordResetCompleteView as DjPasswordResetCompleteView
from django.contrib.auth.views import PasswordResetConfirmView as DjPasswordResetConfirmView
from django.contrib.auth.views import PasswordResetDoneView as DjPasswordResetDoneView
from django.contrib.auth.views import PasswordResetView as DjPasswordResetView
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from comicagg.about.utils import ConsentRequiredMixin, consent_required, consent_show
from comicagg.accounts.utils import (
    send_account_created_email,
    send_account_deleted_email,
    send_email_updated_email,
    send_password_updated_email,
)
from comicagg.typings import AuthenticatedHttpRequest

from .forms import (
    DeleteAccountForm,
    EmailChangeForm,
    LoginForm,
    PasswordResetForm,
    RegisterForm,
)


def logout_view(request: HttpRequest):
    logout(request)
    return redirect("index")


# @consent_required
# @login_required
# def activate(request: AuthenticatedHttpRequest):
#     if request.method == "POST":
#         request.user.is_active = True
#         request.user.save()
#         return redirect("index")
#     return render(request, "accounts/activate.html", {})


class ActivateView(ConsentRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "accounts/activate.html"

    def post(self, request, *args, **kwargs):
        request.user.is_active = True
        request.user.save()
        return redirect("index")


class ProfileView(ConsentRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "accounts/account.html"


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
                return HttpResponseRedirect(next_url) if next_url else redirect("comics:read")
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
        message_text = _("Your account has been created. You can now log in using the username you selected.")
        messages.add_message(request, messages.SUCCESS, message_text)
        send_account_created_email(request, email, username)
        return redirect("accounts:login")


class PasswordResetView(ConsentRequiredMixin, DjPasswordResetView):
    subject_template_name = "accounts/password_reset_subject.html"
    email_template_name = "accounts/password_reset_email.html"
    # html_email_template_name = None
    template_name = "accounts/password_reset_form.html"
    form_class = PasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(DjPasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(DjPasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if type(response) is HttpResponseRedirect and response.url == self.success_url:
            send_password_updated_email(request, self.user.email)
        return response


class PasswordResetCompleteView(DjPasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


class PasswordChangeView(ConsentRequiredMixin, DjPasswordChangeView):
    template_name = "accounts/password_change_form.html"
    success_url = reverse_lazy("accounts:password_change_done")

    def form_valid(self, form):
        request = cast(AuthenticatedHttpRequest, self.request)
        response = super().form_valid(form)
        send_password_updated_email(request, request.user.email)
        return response


class PasswordChangeDoneView(DjPasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"
    title = _("Password change successful")


class UpdateEmailView(ConsentRequiredMixin, LoginRequiredMixin, FormView):
    template_name = "accounts/email_change_form.html"
    form_class = EmailChangeForm
    success_url = reverse_lazy("accounts:email_change_done")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: EmailChangeForm):
        old_email, new_email = form.save()
        if old_email != new_email:
            send_email_updated_email(self.request, new_email, old_email)
        return super().form_valid(form)


class UpdateEmailDoneView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/email_change_done.html"


class DeleteAccountView(ConsentRequiredMixin, LoginRequiredMixin, FormView):
    template_name = "accounts/delete_account_form.html"
    form_class = DeleteAccountForm
    success_url = reverse_lazy("accounts:delete_account_done")

    def form_valid(self, form):
        user = User.objects.get(pk=self.request.user.pk)
        if user.is_superuser:
            raise CannotDeleteSuperuserError()
        logout(self.request)
        user.delete()
        send_account_deleted_email(self.request, user.email)
        return super().form_valid(form)


class CannotDeleteSuperuserError(Exception):
    pass


class DeleteAccountDoneView(TemplateView):
    template_name = "accounts/delete_account_done.html"

import re

from comicagg.utils import render
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import IntegrityError
from django.forms.utils import ErrorList
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.template import Context, loader
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt

from .forms import (
    EmailChangeForm,
    LoginForm,
    PasswordChangeForm,
    PasswordResetForm,
    RegisterForm,
)


def logout_view(request: HttpRequest):
    logout(request)
    # Redirect to a success page.
    return redirect("index")


def login_view(request: HttpRequest):
    context = {}
    context["parent_template"] = "base.html"
    # If the user is authenticated redirect him to index
    if request.user.is_authenticated:
        return redirect("index")
    # If we get data in POST treat this as a login attempt
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            nexturl = form.cleaned_data["next"]
            oauth2 = form.cleaned_data["oauth2"]
            user = authenticate(username=username, password=password)
            if user is not None:
                # From now on the user is logged in
                login(request, user)
                if user.is_active:
                    # Redirect to the page he was requesting.
                    if nexturl:
                        return HttpResponseRedirect(nexturl)
                    else:
                        return redirect("comics:read")
                else:
                    # User was inactive, redirect to activate page
                    return redirect("accounts:activate")
            else:
                if oauth2:
                    context["parent_template"] = "simple_base.html"
                    context["oauth2"] = True
                # Return an 'invalid login' error message.
                context["error"] = _("Username or password not valid!")
                context["form"] = LoginForm(
                    initial={"username": username, "next": nexturl, "oauth2": oauth2}
                )
                return render(request, "accounts/login_form.html", context, "login")
        context["form"] = form
        # Received an invalid login form, so show the login form again
        return render(request, "accounts/login_form.html", context, "login")
    try:
        nexturl = request.GET["next"]
        form = LoginForm(initial={"next": nexturl})
        if nexturl.count("/oauth2/"):
            context["parent_template"] = "simple_base.html"
            context["oauth2"] = True
            form = LoginForm(initial={"next": nexturl, "oauth2": True})
    except:
        form = LoginForm()
    context["form"] = form
    # Show the login form
    return render(request, "accounts/login_form.html", context, "login")


def register(request: HttpRequest):
    logout(request)
    context = {}
    form = RegisterForm()
    if request.POST:
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            password2 = form.cleaned_data["password2"]
            email = form.cleaned_data["email"]
            captcha = form.cleaned_data["captcha"]
            errors = False
            # TODO: Should use validators in the fields instead of the following
            if password != password2:
                errors = True
                msg = _("Passwords don't match!")
                form._errors["password2"] = ErrorList([msg])
            if captcha != "comic":
                errors = True
                msg = _("Wrong word!")
                form._errors["captcha"] = ErrorList([msg])
            if re.compile("[^a-zA-Z0-9_.]").search(username):
                errors = True
                msg = _("Some letters are not valid.")
                form._errors["username"] = ErrorList([msg])
            if len(username) < 3:
                errors = True
                msg = _("Too short.")
                try:
                    form._errors["username"].append(msg)
                except:
                    form._errors["username"] = ErrorList([msg])
            if len(username) > 30:
                errors = True
                msg = _("That long? Really?")
                try:
                    form._errors["username"].append(msg)
                except:
                    form._errors["username"] = ErrorList([msg])
            if not errors:
                try:
                    User.objects.create_user(username, email, password)
                    return redirect("accounts:done", kind="register")
                except IntegrityError:
                    msg = _("That username is already taken. Please choose another.")
                    form._errors["username"] = ErrorList([msg])

    context["form"] = form
    return render(request, "accounts/register.html", context, "register")


def done(request: HttpRequest, kind: str):
    try:
        return render(request, f"accounts/{kind}_done.html", {}, "account")
    except:
        return redirect("index")


def password_reset(request: HttpRequest):
    context = {}
    form = PasswordResetForm()
    if request.POST:
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            username_or_password = form.cleaned_data["username_or_password"]
            # Check if there are valid email add
            users_email = list(User.objects.filter(email__iexact=username_or_password))
            # Check if there is a username
            users_username = list(
                User.objects.filter(username__iexact=username_or_password)
            )
            users = users_email + users_username
            # Create new password and send email
            for user in users:
                new_pass = User.objects.make_random_password()
                user.set_password(new_pass)
                user.save()
                template_file = loader.get_template(
                    "accounts/password_reset_email.html"
                )
                template_context = {
                    "new_password": new_pass,
                    "email": user.email,
                    "domain": settings.SITE_DOMAIN,
                    "site_name": settings.SITE_NAME,
                    "user": user,
                }
                subject = _("Password reset on %(site)s") % {"site": settings.SITE_NAME}
                send_mail(
                    subject,
                    template_file.render(Context(template_context)),
                    None,
                    [user.email],
                )
            return redirect("accounts:done", kind="password_reset")
    context["form"] = form
    return render(request, "accounts/password_reset_form.html", context, "account")


@login_required
def password_change(request: HttpRequest):
    context = {}
    form = PasswordChangeForm()
    if request.POST:
        form = PasswordChangeForm(request.POST)
        # Validate old password
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
    context["form"] = form
    return render(request, "accounts/password_change_form.html", context, "account")


@login_required
def update_email(request: HttpRequest):
    context = {}
    form = EmailChangeForm()
    if request.POST:
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
    context["form"] = form
    return render(request, "accounts/email_change_form.html", context, "account")


@login_required
def view_profile(request: HttpRequest, saved=False):
    return render(request, "accounts/account.html", {}, "account")


@login_required
@csrf_exempt # TODO: Why?
def activate(request: HttpRequest):
    if request.method == "POST":
        request.user.is_active = True
        request.user.save()
        return redirect("index")
    return render(request, "accounts/activate.html", {}, "account")

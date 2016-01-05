# -*- coding: utf-8 -*-
from comicagg.accounts.forms import LoginForm, EmailChangeForm, PasswordChangeForm, PasswordResetForm, ProfileForm, RegisterForm
from comicagg import render
from django.db import IntegrityError
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.forms.utils import ErrorList
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import redirect
from django.template import Context, loader
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
import re

def index(request):
    if request.user.is_authenticated():
        return redirect('comics:read')
    else:
        return redirect('accounts:login')

def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return redirect('index')

def login_view(request):
    context = {}
    context["parent_template"] = "base.html"
    #if user is authenticated redirect him to index
    if request.user.is_authenticated():
        return redirect('index')
    #if we get data in post treat as a login attempt
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            nexturl = form.cleaned_data['next']
            oauth2 = form.cleaned_data['oauth2']
            user = authenticate(username=username, password=password)
            if user is not None:
            #From now on the user is logged in
                login(request, user)
                if user.is_active:
                    # Redirect to the page he was requesting.
                    return HttpResponseRedirect(nexturl)
                else:
                    #User was inactive, redirect to activate page
                    return redirect('accounts:activate')
            else:
                if oauth2:
                    context['parent_template'] = 'simple_base.html'
                    context['oauth2'] = True
                # Return an 'invalid login' error message.
                context['error'] = _('Username or password not valid!')
                context['form'] = LoginForm(initial={'username': username, 'next': nexturl, 'oauth2': oauth2})
                return render(request, 'accounts/login_form.html', context, 'login')
        context['form'] = form
        #received nothing so show login form
        return render(request, 'accounts/login_form.html', context, 'login')
    try:
        nexturl = request.GET['next']
        form = LoginForm(initial={'next': nexturl})
        if  nexturl.count('/oauth2/'):
            context['parent_template'] = 'simple_base.html'
            context['oauth2'] = True
            form = LoginForm(initial={'next': nexturl, 'oauth2': True})
    except:
        form = LoginForm()
    context['form'] = form
    #received nothing so show login form
    return render(request, 'accounts/login_form.html', context, 'login')

def register(request):
    logout(request)
    context = {}
    form = RegisterForm()
    if request.POST:
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']
            email = form.cleaned_data['email']
            captcha = form.cleaned_data['captcha']
            errors = False
            if password != password2:
                errors = True
                msg = _("Passwords don't match!")
                form._errors['password2'] = ErrorList([msg])
            if captcha != 'comic':
                errors = True
                msg = _("Wrong word!")
                form._errors['captcha'] = ErrorList([msg])
            if re.compile('[^a-zA-Z0-9_.]').search(username):
                errors = True
                msg = _("Some letters are not valid.")
                form._errors['username'] = ErrorList([msg])
            if len(username) < 3:
                errors = True
                msg = _("Too short.")
                try:
                    form._errors['username'].append(msg)
                except:
                    form._errors['username'] = ErrorList([msg])
            if len(username) > 30:
                errors = True
                msg = _("That long? Really?")
                try:
                    form._errors['username'].append(msg)
                except:
                    form._errors['username'] = ErrorList([msg])
            if not errors:
                try:
                    User.objects.create_user(username, email, password)
                    return redirect('accounts:done', kind='register')
                except IntegrityError:
                    msg = _("That username is already taken. Please choose another.")
                    form._errors['username'] = ErrorList([msg])

    context['form'] = form
    return render(request, 'accounts/register.html', context, 'register')

def done(request, kind):
    try:
        return render(request, 'accounts/%s_done.html' % kind, {}, 'account')
    except:
        return redirect('index')

def password_reset(request):
    context = {}
    form = PasswordResetForm()
    if request.POST:
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data['data']
            #check if there are valid email add
            users_email = list(User.objects.filter(email__iexact=data))
            #check if there is a username
            users_username = list(User.objects.filter(username__iexact=data))
            users = users_email + users_username
            if users:
                #create new password and send email
                for user in users:
                    new_pass = User.objects.make_random_password()
                    user.set_password(new_pass)
                    user.save()
                    t = loader.get_template('accounts/password_reset_email.html')
                    c = {
                            'new_password': new_pass,
                            'email': user.email,
                            'domain': settings.DOMAIN,
                            'site_name': settings.SITE_NAME,
                            'user': user,
                            }
                    subject = _('Password reset on %(site)s') % { 'site':settings.SITE_NAME }
                    send_mail(subject, t.render(Context(c)), None, [user.email])
            return redirect('accounts:done', kind='password_reset')
    context['form'] = form
    return render(request, 'accounts/password_reset_form.html', context, 'account')

@login_required
def password_change(request):
    context = {}
    form = PasswordChangeForm()
    if request.POST:
        form = PasswordChangeForm(request.POST)
        #check old password
        if form.is_valid():
            old = form.cleaned_data['old_password']
            new1 = form.cleaned_data['new_password1']
            new2 = form.cleaned_data['new_password2']
            if not request.user.check_password(old):
                form.errors['not_valid'] = True
            if new1 != new2:
                form.errors['are_different'] = True
            if not form.errors:
                request.user.set_password(new1)
                request.user.save()
                return redirect('accounts:done', kind='password_change')
    context['form'] = form
    return render(request, 'accounts/password_change_form.html', context, 'account')

@login_required
def email(request):
    context = {}
    form = EmailChangeForm()
    if request.POST:
        form = EmailChangeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            if not request.user.check_password(password):
                form.errors['incorrect_password'] = True
            else:
                request.user.email = email
                request.user.save()
                return redirect('accounts:done', kind='email_change')
    context['form'] = form
    return render(request, 'accounts/email_change_form.html', context, 'account')

@login_required
def edit_profile(request, saved=False):
    return render(request, 'accounts/account.html', {}, 'account')

@login_required
def save_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            p = request.user_profile
            p.hide_read = form.cleaned_data['hide_read']
#            p.sort_by_points = form.cleaned_data['sort_by_points']
            p.alert_new_comics = form.cleaned_data['alert_new_comics']
            nmc = form.cleaned_data['navigation_max_columns']
            if nmc > 0:
                p.navigation_max_columns = form.cleaned_data['navigation_max_columns']
            nmpc = form.cleaned_data['navigation_max_per_column']
            if nmpc > 0:
                p.navigation_max_per_column = form.cleaned_data['navigation_max_per_column']
            p.save()
    return redirect('accounts:profile_saved')

@login_required
def save_color(request):
    if request.method == 'POST':
        try:
            new_color = request.POST['new_color']
        except:
            new_color = None
        if new_color:
            p = request.user_profile
            p.css_color = new_color
            p.save()
            return HttpResponse('0')
    raise Http404

@login_required
@csrf_exempt
def activate(request):
    if request.method == 'POST':
        request.user.is_active = True
        request.user.save()
        return redirect('index')
    return render(request, 'accounts/activate.html', {}, 'account')

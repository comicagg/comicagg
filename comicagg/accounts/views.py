# -*- coding: utf-8 -*-
# Create your views here.
from comicagg.accounts.models import *
from comicagg.agregator.models import Comic
from comicagg import render
from django.db import IntegrityError
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.forms.util import ErrorList
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import Context, loader
from django.utils.translation import ugettext as _
import re

def index(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('read'))
    else:
        return HttpResponseRedirect(reverse('login'))

    #last = Comic.objects.filter(activo=True).filter(ended=False).order_by('-id')[:5]
    #form = LoginForm()
    #return render(request, 'welcome.html', {'last':last, 'form':form})

def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return HttpResponseRedirect(reverse('index'))

def login_view(request):
    context = {}
    #if user is authenticated redirect him to index
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('index'))
    #if we get data in post treat as a login attempt
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            next = form.cleaned_data['next']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    # Redirect to a success page.
                    return HttpResponseRedirect(next)
                else:
                    context['error'] =_('Your have to activate your user first')
                    context['form'] = form
                    return render(request, 'registration/login_form.html', context, 'login')
                    # Return a 'disabled account' error message
            else:
                # Return an 'invalid login' error message.
                context['error'] = _('Username or password not valid!')
                context['form'] = LoginForm(initial={'username': username})
                return render(request, 'registration/login_form.html', context, 'login')
        context['form'] = form
        #received nothing so show login form
        return render(request, 'registration/login_form.html', context, 'login')
    try:
        next = request.GET['next']
        form = LoginForm(initial={'next': next})
    except:
        form = LoginForm()
    context['form'] = form
    #received nothing so show login form
    return render(request, 'registration/login_form.html', context, 'login')

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
                    u = User.objects.create_user(username, email, password)
                    return HttpResponseRedirect(reverse('done', args=['register']))
                except IntegrityError:
                    msg = _("That username is already taken. Please choose another.")
                    form._errors['username'] = ErrorList([msg])

    context['form'] = form
    return render(request, 'registration/register.html', context, 'register')

def done(request, kind):
    try:
        return render(request, 'registration/%s_done.html' % kind, {}, 'account')
    except:
        return HttpResponseRedirect(reverse('index'))

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
            print users
            if users:
                #create new password and send email
                for user in users:
                    new_pass = User.objects.make_random_password()
                    user.set_password(new_pass)
                    user.save()
                    t = loader.get_template('registration/password_reset_email.html')
                    c = {
                            'new_password': new_pass,
                            'email': user.email,
                            'domain': settings.DOMAIN,
                            'site_name': settings.SITE_NAME,
                            'user': user,
                            }
                    send_mail(_('Password reset on %s') % settings.SITE_NAME, t.render(Context(c)), None, [user.email])
            return HttpResponseRedirect(reverse('done', args=['password_reset']))
    context['form'] = form
    return render(request, 'registration/password_reset_form.html', context, 'account')

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
                return HttpResponseRedirect(reverse('done', args=['password_change']))
    context['form'] = form
    return render(request, 'registration/password_change_form.html', context, 'account')

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
                return HttpResponseRedirect(reverse('done', args=['email_change']))
    context['form'] = form
    return render(request, 'registration/email_change_form.html', context, 'account')

@login_required
def edit_profile(request, saved=False):
    p = request.user.get_profile()
    data = {
        'hide_read': p.hide_read,
#        'sort_by_points': p.sort_by_points,
        'alert_new_comics': p.alert_new_comics,
        'navigation_max_columns':p.navigation_max_columns,
        'navigation_max_per_column':p.navigation_max_per_column,
    }
    form = ProfileForm(data)
    return render(request, 'registration/account.html', {'form':form, 'saved':saved}, 'account')

@login_required
def save_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            p = request.user.get_profile()
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
            # Do form processing here...
    return HttpResponseRedirect(reverse('saved_profile'))

@login_required
def save_color(request):
    if request.method == 'POST':
        try:
            new_color = request.POST['new_color']
        except:
            new_color = None
        if new_color:
            p = request.user.get_profile()
            p.css_color = new_color
            p.save()
            return HttpResponse('0')
    raise Http404

@login_required
def activate(request):
    if request.method == 'POST':
        request.user.is_active = True
        request.user.save()
        return HttpResponseRedirect(reverse('index'))
    raise Http404

# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django import forms
from datetime import datetime

# Create your models here.
class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)

    last_read_access = models.DateTimeField()
    new_comics = models.BooleanField(default=False)
    new_blogs = models.BooleanField(default=False)

    hide_read = models.BooleanField(default=True)
    #sort_by_points = models.BooleanField(default=False)

    alert_new_comics = models.BooleanField(default=True)
    alert_new_blog = models.BooleanField(default=True)

    navigation_max_columns = models.IntegerField(default=5)
    navigation_max_per_column = models.IntegerField(default=20)

    css_color = models.CharField(max_length=100, default="blue_white")

    def __unicode__(self):
        return u'%s' % self.user

    def is_active(self):
        if self.user.is_active:
            return True
        return False
    is_active.boolean = True

    class Meta:
        ordering = ['user']
        verbose_name = _('User profile')
        verbose_name_plural = _('User profiles')

class ProfileForm(forms.Form):
    hide_read = forms.BooleanField(required=False)
    #  sort_by_points = forms.BooleanField(required=False)
    alert_new_comics = forms.BooleanField(required=False)
    alert_new_blog = forms.BooleanField(required=False)
    navigation_max_columns = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'size':'2'}))
    navigation_max_per_column = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'size':'2'}))

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    oauth2 = forms.BooleanField(widget=forms.HiddenInput(), required=False)

class EmailChangeForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'size':'35'}))

class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))

class PasswordResetForm(forms.Form):
    data = forms.CharField(widget=forms.PasswordInput(attrs={'size':'35'}))

class RegisterForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'size':'30'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'size':'25'}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'size':'50'}))
    captcha = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}))

def create_account(sender, **kwargs):
    if kwargs['created']:
        up = UserProfile(user=kwargs['instance'], last_read_access=datetime.now())
        up.save()

post_save.connect(create_account, sender=User)

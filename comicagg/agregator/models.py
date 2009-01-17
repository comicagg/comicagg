#coding: utf-8
from comicagg.accounts.models import *
from django.db import models
from django.contrib.auth.models import User
from django import forms
from datetime import datetime, timedelta
import re, urllib
from math import atan, pi, floor

# Create your models here.
class Comic(models.Model):
  name = models.CharField(max_length=255)
  website = models.URLField(verify_exists=False)
  activo = models.BooleanField(default=False)
  notify = models.BooleanField(default=False)
  #ALTER TABLE `agregator_comic` ADD `notify` TINYINT( 1 ) NOT NULL DEFAULT '0';
  ended = models.BooleanField(default=False)
  #ALTER TABLE `agregator_comic` ADD `ended` TINYINT( 1 ) NOT NULL DEFAULT '0';

  #url that points to the web page with the last strip
  url = models.URLField(verify_exists=False)
  #base adress for the image
  base_img = models.CharField(max_length=255)
  #regexp for the image
  regexp = models.CharField(max_length=255)
  #start searching from the end
  backwards = models.BooleanField(default=False)
  #ALTER TABLE `agregator_comic` ADD `backwards` TINYINT( 1 ) NOT NULL DEFAULT '0';

  #url donde esta la direccion a la pagina de la ultima tira
  url2 = models.URLField(null=True, blank=True,verify_exists=False)
  #base address for redirections
  base2 = models.CharField(max_length=255, null=True, blank=True)
  #regexp para encontrar la url de la pagina de la ultima tira
  regexp2 = models.CharField(max_length=255, null=True, blank=True)
  #start searching from the end
  backwards2 = models.BooleanField(default=False)
  #ALTER TABLE `agregator_comic` ADD `backwards2` TINYINT( 1 ) NOT NULL DEFAULT '0';

  referer = models.URLField(null=True, blank=True,verify_exists=False)
  fake_user_agent = models.BooleanField(default=False)
  #ALTER TABLE `agregator_comic` ADD `fake_user_agent` TINYINT( 1 ) NOT NULL DEFAULT '0';

  last_check = models.DateTimeField(blank=True)
  last_image = models.URLField(blank=True,verify_exists=False)

  rating = models.IntegerField(default=0)
  votes = models.IntegerField(default=0)

  add_date = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ['name']

  def __unicode__(self):
    return u'%s' % self.name

  def save(self):
    notify = False
    #si es nuevo y es activo
    if self.notify: #or (not self.id and self.activo):
      notify = True
      self.notify = False
    super(Comic, self).save()
    #avisar de que hay nuevos comics
    if notify:
      users = User.objects.all()
      for user in users:
        try:
          up = user.get_profile()
          #up.last_read_access=datetime.now()
        except:
          up = UserProfile(user=user, last_read_access=datetime.now())
          #por cada usuario poner el campo del perfil new_comics a True
        if up.alert_new_comics:
          print "notifying"
          up.new_comics = True;
          new = NewComic(user=user, comic=self)
          new.save()
        up.save()

  def get_rating(self):
    return self.getRating()

  def getRating(self):
    if not hasattr(self, '__rating'):
      r = 50
      if self.votes > 0:
        #p = self.rating
        #n = self.votes - self.rating
        #x = p - n
        x = 2 * self.rating - self.votes
        if x > 0:
          r = int(((20-atan(x/5.0)/(x/100.0))/40+0.5)*100)
        elif x < 0:
          r = int((0.5-(20-atan(x/5.0)/(x/100.0))/40)*100)
        #porcentaje de votos positivos
        #r = int(floor(self.rating / float(self.votes) * 100))
        #porcentaje de votos negativos
        #n = 100 - r
        #g(x)=2/sqrt(pi)*(x-x^3/3+x^5/10-x^7/42+x^9/216)
      setattr(self, '__rating', r)
    return getattr(self, '__rating')

  def positivevotes(self):
    try:
      r = float(self.rating)/self.votes*100
    except:
      r = 0
    return r

  def is_new_for(self, user):
    return NewComic.objects.filter(comic=self, user=user).count() != 0

class Subscription(models.Model):
  user = models.ForeignKey(User)
  comic = models.ForeignKey(Comic)
  position = models.PositiveIntegerField(blank=True, default=0)

  class Meta:
    ordering = ['user', 'position']

  def __unicode__(self):
    return u'%s - %s' % (self.user, self.comic)

class Request(models.Model):
  user = models.ForeignKey(User)
  url = models.URLField(verify_exists=False)
  comment = models.TextField()

  def __unicode__(self):
    return u'%s - %s' % (self.user, self.url)

class ComicHistory(models.Model):
  comic = models.ForeignKey(Comic)
  date = models.DateTimeField(default=datetime.now())
  url = models.CharField(max_length=255)

  def __unicode__(self):
    return u'%s %s' % (self.comic.name, self.date)

  class Meta:
    ordering = ['-date']


class UnreadComic(models.Model):
  user = models.ForeignKey(User)
  history = models.ForeignKey(ComicHistory)
  comic = models.ForeignKey(Comic)

  def __unicode__(self):
    return u'%s %s' % (self.user, self.history)

  class Meta:
    ordering = ['user', '-history']

class Tag(models.Model):
  user = models.ForeignKey(User)
  comic = models.ForeignKey(Comic)
  name = models.CharField(max_length=255)

  def __unicode__(self):
    return u'%s' % (self.name)
    #return u'%s  - %s - %s' % (self.name, self.comic, self.user)

  class Meta:
    ordering = ['name', 'comic']

class NewComic(models.Model):
  user = models.ForeignKey(User)
  comic = models.ForeignKey(Comic, related_name="new_comics")

  def __unicode__(self):
    return u'%s - %s' % (self.user, self.comic)

class NoMatchException(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class RequestForm(forms.Form):
  url = forms.URLField(widget=forms.TextInput(attrs={'size':70}))
  comment = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':6, 'cols':50}))

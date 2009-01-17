from django.contrib.auth.models import User
from django.db import models
from django import forms

from django.utils.translation import ugettext as _

# Create your models here.
class Faq(models.Model):
  question = models.TextField()
  answer = models.TextField()

  class Meta:
    ordering = ['question']
  #class Admin:
    #list_display = ['question']

class Ticket(models.Model):
  STATUS_CHOICES = (
    ('O', _('Open')),
    ('C', _('Closed')),
  )
  owner = models.ForeignKey(User)
  date = models.DateTimeField(auto_now_add=True)
  status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='O')
  title = models.CharField(max_length=255)
  text = models.TextField()

  def __unicode__(self):
    return u'T%s - %s' % (self.id, self.title)

  def is_closed(self):
    return self.status == 'C'

  def set_open(self):
    self.status = 'O'

  def set_close(self):
    self.status = 'C'

  class Meta:
    ordering = ['-status', '-date']
  #class Admin:
    #list_display = ['owner', 'date', 'title', 'status']

class TicketMessage(models.Model):
  ticket = models.ForeignKey(Ticket, related_name='messages')
  user = models.ForeignKey(User, null=True, blank=True)
  date = models.DateTimeField(auto_now_add=True)
  text = models.TextField()

  def __unicode__(self):
    return u'TM%s - %s' % (self.id, self.ticket)

  class Meta:
    ordering = ['date']
  #class Admin:
    #list_display = ['user', 'date']

class NewTicketForm(forms.Form):
  title = forms.CharField(widget=forms.TextInput(attrs={'size':'60'}), max_length=255, label=_('Title'))
  text = forms.CharField(widget=forms.Textarea(attrs={'cols':'60'}), label=_('Text'))

class ReplyTicketForm(forms.Form):
  text = forms.CharField(widget=forms.Textarea(attrs={'cols':'60'}), label=_('Text'))

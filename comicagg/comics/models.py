# -*- coding: utf-8 -*-
from comicagg.comics.fields import ComicNameField, AltTextField
from comicagg.accounts.models import UserProfile
from datetime import datetime
from django import forms
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.timezone import now as django_now
from math import atan, sqrt


class Comic(models.Model):
    
    name = ComicNameField('Nombre del comic', max_length=255)
    website = models.URLField('Página del comic')
    activo = models.BooleanField('Comic activo', default=False, help_text='')
    notify = models.BooleanField('Notificar comic nuevo a los usuarios', default=False, help_text='Siempre va a aparecer como desactivado aquí. Si se activa, se notifica y se deja la opción desactivada')
    ended = models.BooleanField('Comic terminado', default=False, help_text='Si un comic termina marcar esta opción y desactivarlo también')
    noimages = models.BooleanField('No mostrar imágenes', default=False, help_text='Si no se pueden mostrar las imágenes del comic, marcar para que únicamente salga un texto indicando que se ha actualizado')

    #campo para añadir una funcion custom de actualizacion
    help_text = 'Mirar la <a href="/docs/custom_func/">documentación</a>.'
    custom_func = models.TextField('Función personalizada', null=True, blank=True, help_text=help_text)

    #url that points to the web page with the last strip
    url = models.URLField('Url donde se encuentra la imagen', null=True, blank=True, help_text='Si hay redirección no se utiliza')
    #base adress for the image
    base_img = models.CharField('Url base de la imagen', max_length=255, null=True, blank=True, help_text='Debe contener %s que es donde se pondrá lo capturado por la expresión regular')
    #regexp for the image
    regexp = models.CharField('Expresión regular', max_length=255, null=True, blank=True, help_text='Lo que se quiera capturar se pone <b>entre paréntesis</b>.<br/>Si hace falta usar paréntesis para capturar, se toma como url lo que vaya aquí dentro <b>(?P&lt;url><i>RE de captura</i>)</b>.<br/>Para capturar el texto alternativo, usar la siguiente construcción <b>(?P&lt;alt><i>RE de captura</i>)</b>.')
    #start searching from the end
    backwards = models.BooleanField('Empezar desde el final', default=False)

    #url donde esta la direccion a la pagina de la ultima tira
    url2 = models.URLField('Url donde se encuentra la dirección que contiene la imagen', null=True, blank=True, help_text='Si se pone algo aquí se usa redirección')
    #base address for redirections
    base2 = models.CharField('Url base', max_length=255, null=True, blank=True, help_text='Debe contener %s que es donde se pondrá lo capturado por la expresión regular')
    #regexp para encontrar la url de la pagina de la ultima tira
    regexp2 = models.CharField('Expresión regular', max_length=255, null=True, blank=True, help_text='Lo que se quiera capturar se pone <b>entre paréntesis</b>. Si hace falta usar paréntesis para capturar, se toma como url lo que vaya aquí dentro <b>(?P&lt;url><i>RE de captura</i>)</b>')
    #start searching from the end
    backwards2 = models.BooleanField('Empezar desde el final', default=False)

    referer = models.URLField('Referer', null=True, blank=True, help_text='Si la web del comic comprueba el referer poner aquí alguno para que no dé error')
    fake_user_agent = models.BooleanField('Cambiar User-Agent', default=False, help_text='Si además la web comprueba el User-Agent marcar para conectarse a la web usando otro User-Agent')

    last_check = models.DateTimeField('Última actualización', blank=True)
    last_image = models.URLField('Última imagen', blank=True)
    last_image_alt_text = AltTextField('Texto alternativo', blank=True, null=True) 

    rating = models.IntegerField('Votos positivos', default=0)
    votes = models.IntegerField('Votos totales', default=0)

    add_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        permissions = (
            ("all_images", "Can see all images"),
        )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        notify = False
        #si es nuevo y es activo
        if self.notify: #or (not self.id and self.activo):
            notify = True
            self.notify = False
        super(Comic, self).save(*args, **kwargs)
        #avisar de que hay nuevos comics
        if notify:
            users = User.objects.all()
            for user in users:
                up = UserProfile.objects.get(user=user)
                #por cada usuario poner el campo del perfil new_comics a True
                if up.alert_new_comics:
                    up.new_comics = True;
                    new = NewComic(user=user, comic=self)
                    new.save()
                    up.save()

    def get_rating(self, method='statistic_rating'):
        if not hasattr(self, '__rating'):
            r = getattr(self, method)()
            setattr(self, '__rating', r)
        return getattr(self, '__rating')

    def statistic_rating(self):
        pos = self.rating
        n = self.votes
        if n == 0:
            return 0.0
        #z = Statistics2.pnormaldist(1-power/2)
        z = 3.95
        phat = 1.0*pos/n
        return (phat + z*z/(2*n) - z * sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)

    def mi_rating(self):
        r = 0.5
        if self.votes > 0:
            #p = self.rating
            #n = self.votes - self.rating
            #x = p - n
            x = 2 * self.rating - self.votes
            if x > 0:
                r = ((20-atan(x/5.0)/(x/100.0))/40+0.5)
            elif x < 0:
                r = (0.5-(20-atan(x/5.0)/(x/100.0))/40)
            #porcentaje de votos positivos
            #r = int(floor(self.rating / float(self.votes) * 100))
            #porcentaje de votos negativos
            #n = 100 - r
            #g(x)=2/sqrt(pi)*(x-x^3/3+x^5/10-x^7/42+x^9/216)
        return r

    def positive_votes(self):
        try:
            r = float(self.rating)/self.votes
        except:
            r = 0.0
        return r

    def negative_votes(self):
        return self.votes-self.rating

    _reader_count = None
    def reader_count(self):
        if not self._reader_count:
            self._reader_count = self.subscription_set.count()
        return int(self._reader_count)

    _strip_count = None
    def strip_count(self):
        if not self._strip_count:
            self._strip_count = self.comichistory_set.count()
        return int(self._strip_count)

    def last_image_url(self):
        url = self.last_image
        if self.referer:
            url = reverse('comics:last_image_url', kwargs={'cid':self.id})
        return url

    def last_strip(self):
        return self.comichistory_set.all()[0]

    # User related methods
    # TODO: move this to the UserOperations class
    def is_new_for(self, user):
        """
        Is this comic new to the passed user?
        """
        return NewComic.objects.filter(comic=self, user=user).count() != 0

    def unread_comics_for(self, user):
        return UnreadComic.objects.filter(comic=self, user=user)

def active_comics():
    """
    It will return only comics that an user can follow so no inactive or ended comics.
    """
    return Comic.objects.exclude(activo=False, ended=True)

class Subscription(models.Model):
    user = models.ForeignKey(User)
    comic = models.ForeignKey(Comic)
    position = models.PositiveIntegerField(blank=True, default=0)

    def __str__(self):
        return '%s - %s' % (self.user, self.comic)

    def delete(self, *args, **kwargs):
        #delete related unreadcomics
        UnreadComic.objects.filter(user=self.user, comic=self.comic).delete()
        super(Subscription, self).delete(*args, **kwargs)

    class Meta:
        ordering = ['user', 'position']

class Request(models.Model):
    user = models.ForeignKey(User)
    url = models.URLField()
    comment = models.TextField(blank=True, null=True, default="")
    admin_comment = models.TextField(blank=True, null=True, default="")
    done = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)

    class Meta:
        ordering = ['id', '-done']

    def __str__(self):
        return '%s - %s' % (self.user, self.url)

class ComicHistory(models.Model):
    comic = models.ForeignKey(Comic)
    date = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=255)
    alt_text = AltTextField('Texto alternativo', blank=True, null=True)

    def __str__(self):
        return '%s %s' % (self.comic.name, self.date)

    def image_url(self):
        url = self.url
        if self.comic.referer:
            url = reverse('comics:history_url', kwargs={'hid':self.id})
        return url

    class Meta:
        ordering = ['-id']
        get_latest_by = "date"



class UnreadComic(models.Model):
    user = models.ForeignKey(User)
    history = models.ForeignKey(ComicHistory)
    comic = models.ForeignKey(Comic)
    
    def __str__(self):
        return '%s %s' % (self.user, self.history)
    
    class Meta:
        ordering = ['user', '-history']

class Tag(models.Model):
    user = models.ForeignKey(User)
    comic = models.ForeignKey(Comic)
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return '%s' % (self.name)
        #return '%s  - %s - %s' % (self.name, self.comic, self.user)
    
    class Meta:
        ordering = ['name', 'comic']

class NewComic(models.Model):
    user = models.ForeignKey(User)
    comic = models.ForeignKey(Comic, related_name="new_comics")
    
    def __str__(self):
        return '%s - %s' % (self.user, self.comic)

class NoMatchException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class RequestForm(forms.Form):
    url = forms.URLField(widget=forms.TextInput(attrs={'size':50}))
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':3, 'cols':40}))

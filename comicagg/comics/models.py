# -*- coding: utf-8 -*-
from math import atan, sqrt
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from comicagg.comics.fields import ComicNameField, AltTextField
from comicagg.accounts.models import UserProfile

class Comic(models.Model):
    """
    Comics can be: A active, E ended
    
    E/A T F
    T   - 2
    F   1 3
    1. Active AND not Ended - all ok, ongoing
    2. Not active AND Ended - finished
    3. Not active and not Ended - not working, needs fixing
    So visible to the user should be 1 and 2
    """

    name = ComicNameField('Name', max_length=255)
    website = models.URLField("Website")
    active = models.BooleanField('Is active?', default=False, help_text='The comic is ongoing and gets epdated regularly.')
    notify = models.BooleanField('Notify the users?', default=False,
        help_text="""This is always disabled. If it's enabled when saving the comic, the users will be notified of the new comic.""")
    ended = models.BooleanField('Has ended?', default=False,
        help_text='Check this if the comic has ended. Also mark it as inactive.')
    no_images = models.BooleanField("Don't show images?", default=False,
        help_text='Use it to hide the images of the comic, but allow a notification to the users.')

    custom_func = models.TextField('Custom update function', null=True, blank=True,
        help_text='Check the <a href="/docs/custom_func/">docs</a> for reference.')

    # First regex section
    url = models.URLField('URL of the page where the image can be found', null=True, blank=True,
        help_text='If the redirection URL is used, this field will not be used.')
    base_img = models.CharField('Base URL for the image URL', max_length=255, null=True, blank=True,
        help_text='It must contain the placeholder <b>%s</b> which will be replaced with whatever matches in the regex.')
    regexp = models.CharField('Regular expression', max_length=255, null=True, blank=True,
        help_text="""It must contain one group (between parentheses) that matches the URL of the image.
        Named groups can also be used:<br/>
        - <i>url</i> for the URL of the image: (?P&lt;url>.+)<br/>
        - <i>alt</i> for the alternative text of the image: (?P&lt;alt>.+)""")
    backwards = models.BooleanField('Check backwards.', default=False,
        help_text="Read the page backwards by line (last line first).")

    # Second regex section
    url2 = models.URLField('URL where the page of the image can be found', null=True, blank=True,
        help_text="""Setting this enables the redirection. The engine will open this URL and
        use the regex in this section to search for the URL of the page where the image can be found.""")
    base2 = models.CharField('Base URL for the page URL', max_length=255, null=True, blank=True,
        help_text='It must contain the placeholder <b>%s</b> which will be replaced with whatever matches in the regex.')
    regexp2 = models.CharField('Regular expression', max_length=255, null=True, blank=True,
        help_text="""It must contain one group (between parentheses) that matches the URL of the page.
        Named groups can also be used:<br/>
        - <i>url</i> for the URL of the page: (?P&lt;url>.+)""")
    backwards2 = models.BooleanField('Check backwards.', default=False,
        help_text="Read the page backwards by line (last line first).")

    # Other settings
    # FUTURE: Consider removing these two and always use the first URL as referer and mask the User-Agent.
    referer = models.URLField('Referer', null=True, blank=True,
        help_text='Set this to a URL that the web will accept as referer when getting an update.')
    fake_user_agent = models.BooleanField('Change User-Agent', default=False,
        help_text='Si además la web comprueba el User-Agent marcar para conectarse a la web usando otro User-Agent')

    last_update = models.DateTimeField('Last update', blank=True)
    last_image = models.URLField('Last image URL', blank=True)
    last_image_alt_text = AltTextField('Last image alt text', blank=True, null=True)

    positive_votes = models.IntegerField('Positive votes', default=0)
    total_votes = models.IntegerField('Total votes', default=0)

    add_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        permissions = (
            ("all_images", "Can see all images"),
            )

    def __init__(self, *args, **kwargs):
        super(Comic, self).__init__(*args, **kwargs)
        self._reader_count = None
        self._strip_count = None

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        notify = False
        # If the user saved this with the notify field to true
        if self.notify:
            notify = True
            self.notify = False
        super(Comic, self).save(*args, **kwargs)
        if notify:
            # Create a NewComic object for each user
            users = User.objects.all()
            for user in users:
                up = UserProfile.objects.get(user=user)
                if up.alert_new_comics:
                    up.new_comics = True
                    new = NewComic(user=user, comic=self)
                    new.save()
                    up.save()

    def get_rating(self, method='statistic_rating'):
        if not hasattr(self, '__rating'):
            r = getattr(self, method)()
            setattr(self, '__rating', r)
        return getattr(self, '__rating')

    def statistic_rating(self):
        pos = self.positive_votes
        n = self.total_votes
        if n == 0:
            return 0.0
        #z = Statistics2.pnormaldist(1-power/2)
        z = 3.95
        phat = 1.0*pos/n
        return (phat+z*z/(2*n)-z*sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)

    def mi_rating(self):
        r = 0.5
        if self.total_votes > 0:
            #p = self.positive_votes
            #n = self.total_votes - self.positive_votes
            #x = p - n
            x = 2 * self.positive_votes - self.total_votes
            if x > 0:
                r = ((20-atan(x/5.0)/(x/100.0))/40+0.5)
            elif x < 0:
                r = (0.5-(20-atan(x/5.0)/(x/100.0))/40)
            #porcentaje de votos positivos
            #r = int(floor(self.positive_votes / float(self.total_votes) * 100))
            #porcentaje de votos negativos
            #n = 100 - r
            #g(x)=2/sqrt(pi)*(x-x^3/3+x^5/10-x^7/42+x^9/216)
        return r

    def positive_votes_perc(self):
        try:
            r = float(self.positive_votes) / self.total_votes
        except:
            r = 0.0
        return r

    def negative_votes(self):
        return self.total_votes - self.positive_votes

    def reader_count(self):
        if not self._reader_count:
            self._reader_count = self.subscription_set.count()
        return int(self._reader_count)

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
    # FUTURE: Remove this? Still used in views
    def unread_comics_for(self, user):
        return UnreadComic.objects.filter(comic=self, user=user)

# FUTURE: We may want to move this elsewhere
def active_comics():
    """Returns a QuerySet of Comic objects that a user can follow meaning only active and not ended."""
    return Comic.objects.exclude(active=False, ended=True)

class Subscription(models.Model):
    """A user follows a certain comic and the position of the comic in the reading list."""

    user = models.ForeignKey(User)
    comic = models.ForeignKey(Comic)
    position = models.PositiveIntegerField(blank=True, default=0)

    class Meta:
        ordering = ['user', 'position']

    def __str__(self):
        return '%s - %s' % (self.user, self.comic)

    def delete(self, *args, **kwargs):
        # Delete the related unread comics
        UnreadComic.objects.filter(user=self.user, comic=self.comic).delete()
        super(Subscription, self).delete(*args, **kwargs)

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

# FUTURE: Rename this to ComicStrip
class ComicHistory(models.Model):
    comic = models.ForeignKey(Comic)
    date = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=255)
    alt_text = AltTextField('Alternative text', blank=True, null=True)

    class Meta:
        ordering = ['-id']
        get_latest_by = "date"

    def __str__(self):
        return '%s %s' % (self.comic.name, self.date)

    def image_url(self):
        url = self.url
        if self.comic.referer:
            url = reverse('comics:history_url', kwargs={'hid':self.id})
        return url

class UnreadComic(models.Model):
    user = models.ForeignKey(User)
    history = models.ForeignKey(ComicHistory)
    comic = models.ForeignKey(Comic)
    
    class Meta:
        ordering = ['user', '-history']

    def __str__(self):
        return '%s %s' % (self.user, self.history)
    

class Tag(models.Model):
    user = models.ForeignKey(User)
    comic = models.ForeignKey(Comic)
    name = models.CharField(max_length=255)
    
    class Meta:
        ordering = ['name', 'comic']

    def __str__(self):
        return '%s' % (self.name)
        #return '%s  - %s - %s' % (self.name, self.comic, self.user)
    
class NewComic(models.Model):
    user = models.ForeignKey(User)
    comic = models.ForeignKey(Comic, related_name="new_comics")
    
    def __str__(self):
        return '%s - %s' % (self.user, self.comic)

from math import atan, sqrt
from typing import Any

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from .fields import AltTextField, ComicNameField
from .managers import ComicManager, UnreadStripManager, SubscriptionManager


class Comic(models.Model):
    """
    Comics can be: A active, E ended

    E/A T F
    T   - 2
    F   1 3
    1. Active AND not Ended - all ok, ongoing
    2. Not active AND Ended - finished
    3. Not active AND not Ended - not working, needs fixing
    So visible to the user should be 1 and 2
    """

    name = ComicNameField("Name", max_length=255)
    website = models.URLField("Website")
    active = models.BooleanField(
        "Is active?",
        default=False,
        help_text="The comic is ongoing and gets updated regularly.",
    )
    notify = models.BooleanField(
        "Notify the users?",
        default=False,
        help_text="""This is always disabled. If it's enabled when saving the comic, the users will be notified of the new comic.""",
    )
    ended = models.BooleanField(
        "Has ended?",
        default=False,
        help_text="Check this if the comic has ended. Also mark it as inactive.",
    )
    no_images = models.BooleanField(
        "Don't show images?",
        default=False,
        help_text="Use it to hide the images of the comic, but allow a notification to the users.",
    )
    add_date = models.DateTimeField(auto_now_add=True)

    # Update fields
    custom_func = models.TextField(
        "Custom update function",
        null=True,
        blank=True,
        help_text='Check the <a href="/admin/docs/custom_update/">docs</a> for reference.',
    )

    # First regex section
    re1_url = models.URLField(
        "URL of the page where the image can be found",
        null=True,
        blank=True,
        help_text="If the redirection URL is used, this field will not be used.",
    )
    re1_base = models.CharField(
        "Base URL for the image URL",
        max_length=255,
        null=True,
        blank=True,
        help_text="It must contain the placeholder <b>%s</b> which will be replaced with whatever matches in the regex.",
    )
    re1_re = models.CharField(
        "Regular expression",
        max_length=255,
        null=True,
        blank=True,
        help_text="""It must contain one group (between parentheses) that matches the URL of the image.
        Named groups can also be used:<br/>
        - <i>url</i> for the URL of the image: (?P&lt;url>.+)<br/>
        - <i>alt</i> for the alternative text of the image: (?P&lt;alt>.+)""",
    )
    re1_backwards = models.BooleanField(
        "Check backwards.",
        default=False,
        help_text="Read the page backwards by line (last line first).",
    )

    # Second regex section
    re2_url = models.URLField(
        "URL where the page of the image can be found",
        null=True,
        blank=True,
        help_text="""Setting this enables the redirection. The engine will open this URL and
        use the regex in this section to search for the URL of the page where the image can be found.""",
    )
    re2_base = models.CharField(
        "Base URL for the page URL",
        max_length=255,
        null=True,
        blank=True,
        help_text="It must contain the placeholder <b>%s</b> which will be replaced with whatever matches in the regex.",
    )
    re2_re = models.CharField(
        "Regular expression",
        max_length=255,
        null=True,
        blank=True,
        help_text="""It must contain one group (between parentheses) that matches the URL of the page.
        Named groups can also be used:<br/>
        - <i>url</i> for the URL of the page: (?P&lt;url>.+)""",
    )
    re2_backwards = models.BooleanField(
        "Check backwards.",
        default=False,
        help_text="Read the page backwards by line (last line first).",
    )

    # Other settings
    # FUTURE: Consider removing this and always use the first URL as referrer
    referrer = models.URLField(
        "Referrer",
        null=True,
        blank=True,
        help_text="Set this to a URL that the web will accept as referrer when getting an update.",
    )

    # Last update
    last_update = models.DateTimeField("Last successful update", blank=True, null=True)
    last_update_status = models.TextField(
        "Last update status",
        blank=True,
        null=True,
        help_text="Status of the last update run.",
    )
    last_image = models.URLField("Last image URL", blank=True)
    last_image_alt_text = AltTextField("Last image alt text", blank=True, null=True)

    # Ratings
    positive_votes = models.IntegerField("Positive votes", default=0)
    total_votes = models.IntegerField("Total votes", default=0)

    # Only for typing errors
    id: int
    subscription_set: SubscriptionManager
    strip_set: Any

    objects = ComicManager()

    class Meta:
        ordering = ["name"]
        permissions = (("all_images", "Can see all images"),)

    def __str__(self):
        return self.name

    def __lt__(self, other: "Comic"):
        """To allow ordering using list.sort()"""
        return self.get_rating() < other.get_rating()

    def save(self, *args, **kwargs):
        # If the user saved this with the notify field to true
        should_notify = self.notify
        self.notify = False
        super().save(*args, **kwargs)
        if should_notify:
            # Create a NewComic object for each user
            users = User.objects.all()
            for user in users:
                new_comic = NewComic(user=user, comic=self)
                new_comic.save()

    def get_rating(self, method="statistic_rating"):
        if not hasattr(self, "__rating"):
            rating = getattr(self, method)()
            setattr(self, "__rating", rating)
        return getattr(self, "__rating")

    def statistic_rating(self):
        pos = self.positive_votes
        n = self.total_votes
        if n == 0:
            return 0.0
        # z = Statistics2.pnormaldist(1-power/2)
        z = 3.95
        phat = 1.0 * pos / n
        return (
            phat
            + z**2 / (2 * n)
            - z * sqrt((phat * (1 - phat) + z**2 / (4 * n)) / n)
        ) / (1 + z**2 / n)

    def mi_rating(self):
        r = 0.5
        if self.total_votes > 0:
            # p = self.positive_votes
            # n = self.total_votes - self.positive_votes
            # x = p - n
            x = 2 * self.positive_votes - self.total_votes
            if x > 0:
                r = (20 - atan(x / 5.0) / (x / 100.0)) / 40 + 0.5
            elif x < 0:
                r = 0.5 - (20 - atan(x / 5.0) / (x / 100.0)) / 40
            # porcentaje de votos positivos
            # r = int(floor(self.positive_votes / float(self.total_votes) * 100))
            # porcentaje de votos negativos
            # n = 100 - r
            # g(x)=2/sqrt(pi)*(x-x^3/3+x^5/10-x^7/42+x^9/216)
        return r

    def positive_votes_perc(self):
        try:
            r = float(self.positive_votes) / self.total_votes
        except Exception:
            r = 0.0
        return r

    @property
    def negative_votes(self):
        return self.total_votes - self.positive_votes

    @cached_property
    def reader_count(self):
        return int(self.subscription_set.count())

    @cached_property
    def strip_count(self):
        return int(self.strip_set.count())

    def last_image_url(self):
        """Return last_image or a reversed URL if a referrer is used."""
        return (
            reverse("comics:last_image_url", kwargs={"comic_id": self.id})
            if self.referrer
            else self.last_image
        )

    @cached_property
    def last_strip(self):
        return self.strip_set.all()[0]


class Subscription(models.Model):
    """A comic followed by a user and its position in the reading list."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comic = models.ForeignKey(Comic, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(blank=True, default=0)

    objects = SubscriptionManager()

    class Meta:
        ordering = ["user", "position"]

    def __str__(self):
        return f"{self.user} - {self.comic}"

    def delete(self, *args, **kwargs):
        # Delete the related unread comics
        UnreadStrip.objects.filter(user=self.user, comic=self.comic).delete()
        super().delete(*args, **kwargs)


class Request(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    url = models.URLField()
    comment = models.TextField(blank=True, null=True, default="")
    admin_comment = models.TextField(blank=True, null=True, default="")
    done = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)

    class Meta:
        ordering = ["id", "-done"]

    def __str__(self):
        return f"{self.user} - {self.url}"


class Strip(models.Model):
    comic = models.ForeignKey(Comic, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=255)
    alt_text = AltTextField("Alternative text", blank=True, null=True)

    # For type errors only
    id: int

    class Meta:
        ordering = ["-id"]
        get_latest_by = "date"

    def __str__(self):
        return f"{self.comic.name} - {self.date}"

    def image_url(self):
        url = self.url
        if self.comic.referrer:
            url = reverse("comics:strip_url", kwargs={"strip_id": self.id})
        return url


class UnreadStrip(models.Model):
    """A strip that the user has not read yet."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    strip = models.ForeignKey(Strip, on_delete=models.CASCADE)
    comic = models.ForeignKey(Comic, on_delete=models.CASCADE)

    objects = UnreadStripManager()

    class Meta:
        ordering = ["user", "-strip"]

    def __str__(self):
        return f"{self.user} {self.strip}"


class Tag(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    comic = models.ForeignKey(Comic, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name", "comic"]

    def __str__(self):
        return self.name
        # return '%s  - %s - %s' % (self.name, self.comic, self.user)


class NewComic(models.Model):
    """Used to mark a comic as new for a user so that he can be notified."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comic = models.ForeignKey(
        Comic, on_delete=models.CASCADE, related_name="new_comics"
    )

    def __str__(self):
        return f"{self.user} - {self.comic}"

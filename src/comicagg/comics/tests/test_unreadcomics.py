from django.test import TestCase

from comicagg.accounts.models import User
from comicagg.comics.models import Comic


class UnreadComicTestCase(TestCase):
    fixtures = ["users.json", "comics.json", "strips.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.comic_active = Comic.objects.get(name="Active")
        self.comic_ended = Comic.objects.get(name="Ended")
        self.comic_inactive = Comic.objects.get(name="Inactive")
        self.comic_inactive_ended = Comic.objects.get(name="InactiveEnded")

    # ########################
    # #   Test User.strips   #
    # ########################

    def test_strips_no_subscriptions(self):
        """No subscriptions means no unread comics."""
        strips = self.user.unread_strips().count()

        self.assertEqual(strips, 0)

    def test_strips_subscriptions(self):
        """Should return active and ended unreads."""
        self.user.subscription_set.create(comic=self.comic_active)
        self.user.subscription_set.create(comic=self.comic_ended)
        self.user.subscription_set.create(comic=self.comic_inactive)
        self.user.subscription_set.create(comic=self.comic_inactive_ended)
        strip_active = self.comic_active.strip_set.first()
        strip_ended = self.comic_ended.strip_set.first()
        strip_inactive = self.comic_inactive.strip_set.first()
        strip_inactiveended = self.comic_inactive_ended.strip_set.first()
        self.user.unreadcomic_set.create(comic=self.comic_active, strip=strip_active)
        self.user.unreadcomic_set.create(comic=self.comic_ended, strip=strip_ended)
        self.user.unreadcomic_set.create(
            comic=self.comic_inactive, strip=strip_inactive
        )
        self.user.unreadcomic_set.create(
            comic=self.comic_inactive_ended, strip=strip_inactiveended
        )

        active_subscriptions = self.user.unread_strips().count()

        self.assertEqual(active_subscriptions, 2)

    # ###############################
    # #   Test User.unread_comics   #
    # ###############################

    def test_unread_comics_no_subscriptions(self):
        """Should return an empty list."""
        unreads = self.user.comics_unread()

        self.assertEqual(len(unreads), 0)

    def test_unread_comics_subscriptions(self):
        """Should return an empty list."""
        self.user.subscription_set.create(comic=self.comic_active)
        self.user.subscription_set.create(comic=self.comic_ended)
        self.user.subscription_set.create(comic=self.comic_inactive)
        self.user.subscription_set.create(comic=self.comic_inactive_ended)

        unreads = self.user.comics_unread()

        self.assertEqual(len(unreads), 0)

    def test_unread_comics_subscriptions_unreads(self):
        """Should return a non-empty list."""
        self.user.subscription_set.create(comic=self.comic_active)
        self.user.subscription_set.create(comic=self.comic_ended)
        self.user.subscription_set.create(comic=self.comic_inactive)
        self.user.subscription_set.create(comic=self.comic_inactive_ended)
        strip_active = self.comic_active.strip_set.first()
        strip_ended = self.comic_ended.strip_set.first()
        strip_inactive = self.comic_inactive.strip_set.first()
        strip_inactiveended = self.comic_inactive_ended.strip_set.first()
        self.user.unreadcomic_set.create(comic=self.comic_active, strip=strip_active)
        self.user.unreadcomic_set.create(comic=self.comic_ended, strip=strip_ended)
        self.user.unreadcomic_set.create(
            comic=self.comic_inactive, strip=strip_inactive
        )
        self.user.unreadcomic_set.create(
            comic=self.comic_inactive_ended, strip=strip_inactiveended
        )

        unreads = self.user.comics_unread()

        self.assertEqual(len(unreads), 2)

from django.test import TestCase
from comicagg.accounts.models import User

from comicagg.comics.models import Comic, Subscription


# TODO: Test the order of the subscriptions
class SubscriptionsTestCase(TestCase):
    fixtures = ["users.json", "comics.json", "strips.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.comic_active = Comic.objects.get(name="Active")
        self.comic_ended = Comic.objects.get(name="Ended")
        self.comic_inactive = Comic.objects.get(name="Inactive")
        self.comic_inactive_ended = Comic.objects.get(name="InactiveEnded")

    # ###################################
    # #   Test User.subscriptions_all   #
    # ###################################

    def test_all_subscriptions_empty(self):
        subscriptions = self.user.subscriptions().count()
        is_subscribed = self.user.is_subscribed(self.comic_active)

        self.assertEqual(subscriptions, 0)
        self.assertFalse(is_subscribed, "Comic cannot be subscribed")

    def test_all_subscriptions(self):
        """Should return active and ended comics."""
        self.user.subscription_set.create(comic=self.comic_active)  # Yes
        self.user.subscription_set.create(comic=self.comic_ended)  # Yes
        self.user.subscription_set.create(comic=self.comic_inactive_ended)
        self.user.subscription_set.create(comic=self.comic_inactive)

        all_subscriptions = self.user.subscriptions().count()

        self.assertEqual(all_subscriptions, 2)

    # ######################################
    # #   Test User.subscriptions_active   #
    # ######################################

    def test_active_subscriptions_empty(self):
        subscriptions = self.user.subscriptions_active().count()

        self.assertEqual(subscriptions, 0)

    def test_active_subscriptions(self):
        """Should only return active comics."""
        self.user.subscription_set.create(comic=self.comic_active)  # Yes
        self.user.subscription_set.create(comic=self.comic_ended)
        self.user.subscription_set.create(comic=self.comic_inactive)
        self.user.subscription_set.create(comic=self.comic_inactive_ended)

        active_subscriptions = self.user.subscriptions_active().count()

        self.assertEqual(active_subscriptions, 1)

    # ###################################
    # #   Test User.comics_subscribed   #
    # ###################################

    def test_comics_subscribed_all_empty(self):
        comics = list(self.user.comics_subscribed())

        self.assertEqual(len(comics), 0)

    def test_comics_subscribed_all_subscriptions(self):
        self.user.subscription_set.create(comic=self.comic_active, position=1)  # Yes
        self.user.subscription_set.create(comic=self.comic_ended, position=2)  # Yes
        self.user.subscription_set.create(comic=self.comic_inactive)
        self.user.subscription_set.create(comic=self.comic_inactive_ended)

        comics = list(self.user.comics_subscribed())

        self.assertEqual(len(comics), 2)
        self.assertIsInstance(comics[0], Comic)
        self.assertListEqual(comics, [self.comic_active, self.comic_ended])

    # ###################################
    # #   Test User.is_subscribed   #
    # ###################################

    def test_is_subscribed_empty(self):
        is_subscribed = self.user.is_subscribed(self.comic_active)

        self.assertFalse(is_subscribed, "Comic cannot be subscribed")

    def test_is_subscribed(self):
        """Should return active and ended comics."""
        self.user.subscription_set.create(comic=self.comic_active)  # Yes
        self.user.subscription_set.create(comic=self.comic_ended)  # Yes
        self.user.subscription_set.create(comic=self.comic_inactive)  # No
        self.user.subscription_set.create(comic=self.comic_inactive_ended)  # No

        active = self.user.is_subscribed(self.comic_active)
        ended = self.user.is_subscribed(self.comic_ended)
        inactive = self.user.is_subscribed(self.comic_inactive)
        inactive_ended = self.user.is_subscribed(self.comic_inactive_ended)

        self.assertTrue(active)
        self.assertTrue(ended)
        self.assertFalse(inactive)
        self.assertFalse(inactive_ended)

    # ###########################
    # #   Test User.subscribe   #
    # ###########################

    def test_subscribe_comic_active_empty(self):
        self.user.subscribe(self.comic_active)

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(subscription_count, 1)
        self.assertEqual(strip_count, 1)

    def test_subscribe_comic_active_subscriptions(self):
        self.user.subscription_set.create(comic=self.comic_ended, position=1)
        self.user.subscribe(self.comic_active)

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 2)
        self.assertEqual(strip_count, 1)
        self.assertListEqual(comics, [self.comic_ended, self.comic_active])

    def test_subscribe_comic_ended(self):
        with self.assertRaises(Exception, msg="Cannot subscribe to ended comics"):
            self.user.subscribe(self.comic_ended)

    def test_subscribe_comic_inactive(self):
        with self.assertRaises(Exception, msg="Cannot subscribe to inactive comics"):
            self.user.subscribe(self.comic_inactive)

    def test_subscribe_comic_inactive_ended(self):
        with self.assertRaises(
            Exception, msg="Cannot subscribe to inactive and ended comics"
        ):
            self.user.subscribe(self.comic_inactive_ended)

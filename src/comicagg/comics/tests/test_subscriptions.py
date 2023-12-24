from django.test import TestCase
from comicagg.accounts.models import InvalidComicError, User

from comicagg.comics.models import Comic, Subscription


# TODO: Test the order of the subscriptions
class SubscriptionsTestCase(TestCase):
    fixtures = ["users.json", "comics.json", "strips.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.comic_active = Comic.objects.get(name="Active")
        self.comic_active2 = Comic.objects.get(name="Active2")
        self.comic_ended = Comic.objects.get(name="Ended")
        self.comic_inactive = Comic.objects.get(name="Inactive")
        self.comic_inactive_ended = Comic.objects.get(name="InactiveEnded")
        self.strip_active = self.comic_active.strip_set.first()
        self.strip_ended = self.comic_ended.strip_set.first()
        self.strip_inactive = self.comic_inactive.strip_set.first()
        self.strip_inactiveended = self.comic_inactive_ended.strip_set.first()
        # Set up a second user
        self.user2 = User.objects.get(pk=2)
        self.user2.subscription_set.create(comic=self.comic_active, position=1)
        self.user2.subscription_set.create(comic=self.comic_ended, position=2)
        self.user2.subscription_set.create(comic=self.comic_inactive, position=3)
        self.user2.subscription_set.create(comic=self.comic_inactive_ended, position=4)

    def add_subscriptions(self):
        self.user.subscription_set.create(comic=self.comic_active, position=1)
        self.user.subscription_set.create(comic=self.comic_ended, position=2)
        self.user.subscription_set.create(comic=self.comic_inactive, position=3)
        self.user.subscription_set.create(comic=self.comic_inactive_ended, position=4)

    def add_unread_strips(self):
        self.user.unreadstrip_set.create(
            comic=self.comic_active, strip=self.strip_active
        )
        self.user.unreadstrip_set.create(comic=self.comic_ended, strip=self.strip_ended)
        self.user.unreadstrip_set.create(
            comic=self.comic_inactive, strip=self.strip_inactive
        )
        self.user.unreadstrip_set.create(
            comic=self.comic_inactive_ended, strip=self.strip_inactiveended
        )

    # ###############################
    # #   Test User.subscriptions   #
    # ###############################

    def test_subscriptions_empty(self):
        """Should return an empty list."""
        subscriptions = self.user.subscriptions().count()
        is_subscribed = self.user.is_subscribed(self.comic_active)

        self.assertEqual(subscriptions, 0)
        self.assertFalse(is_subscribed, "Comic cannot be subscribed")

    def test_subscriptions(self):
        """Should return active and ended comics."""
        self.add_subscriptions()

        all_subscriptions = self.user.subscriptions().count()

        self.assertEqual(all_subscriptions, 2)

    # ######################################
    # #   Test User.subscriptions_active   #
    # ######################################

    def test_active_subscriptions_empty(self):
        """Should return an empty list."""
        subscriptions = self.user.subscriptions_active().count()

        self.assertEqual(subscriptions, 0)

    def test_active_subscriptions(self):
        """Should only return active comics."""
        self.add_subscriptions()

        active_subscriptions = self.user.subscriptions_active().count()

        self.assertEqual(active_subscriptions, 1)

    # ###################################
    # #   Test User.comics_subscribed   #
    # ###################################

    def test_comics_subscribed_all_empty(self):
        """Should return an empty list."""
        comics = list(self.user.comics_subscribed())

        self.assertEqual(len(comics), 0)

    def test_comics_subscribed_all_subscriptions(self):
        """Should return active and ended comics."""
        self.add_subscriptions()

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
        self.add_subscriptions()

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
        with self.assertRaises(
            InvalidComicError, msg="Cannot subscribe to ended comics"
        ):
            self.user.subscribe(self.comic_ended)

    def test_subscribe_comic_inactive(self):
        with self.assertRaises(
            InvalidComicError, msg="Cannot subscribe to inactive comics"
        ):
            self.user.subscribe(self.comic_inactive)

    def test_subscribe_comic_inactive_ended(self):
        with self.assertRaises(
            InvalidComicError, msg="Cannot subscribe to inactive and ended comics"
        ):
            self.user.subscribe(self.comic_inactive_ended)

    # ################################
    # #   Test User.subscribe_list   #
    # ################################

    def test_subscribe_list_empty(self):
        """Should not create any subscriptions."""
        self.user.subscribe_list([])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(subscription_count, 0)
        self.assertEqual(strip_count, 0)

    def test_subscribe_list(self):
        """Should create subscriptions for active and ended comics."""
        self.user.subscribe_list([self.comic_active.id, self.comic_active2.id])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 2)
        self.assertEqual(strip_count, 1)
        self.assertListEqual(comics, [self.comic_active, self.comic_active2])

    def test_subscribe_list_ended(self):
        """Should not create subscriptions for ended comics."""
        self.user.subscribe_list([self.comic_ended.id])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(subscription_count, 0)
        self.assertEqual(strip_count, 0)

    def test_subscribe_list_inactive(self):
        """Should not create subscriptions for inactive comics."""
        self.user.subscribe_list([self.comic_inactive.id])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(subscription_count, 0)
        self.assertEqual(strip_count, 0)

    def test_subscribe_list_inactive_ended(self):
        """Should not create subscriptions for inactive and ended comics."""
        self.user.subscribe_list([self.comic_inactive_ended.id])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(subscription_count, 0)
        self.assertEqual(strip_count, 0)

    def test_subscribe_list_duplicates(self):
        """Should not create duplicate subscriptions."""
        self.user.subscribe_list(
            [self.comic_active.id, self.comic_active2.id, self.comic_active.id]
        )

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 2)
        self.assertEqual(strip_count, 1)
        self.assertListEqual(comics, [self.comic_active, self.comic_active2])

    def test_subscribe_list_mixed(self):
        """Should not create subscriptions for inactive and ended comics."""
        self.user.subscribe_list(
            [
                self.comic_active.id,
                self.comic_ended.id,
                self.comic_inactive.id,
                self.comic_inactive_ended.id,
                self.comic_active2.id,
            ]
        )

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 2)
        self.assertEqual(strip_count, 1)
        self.assertListEqual(comics, [self.comic_active, self.comic_active2])

    # #############################
    # #   Test User.unsubscribe   #
    # #############################

    def test_unsubscribe_comic_not_subscribed_empty(self):
        """Should not change anything since the comic is not subscribed."""
        self.user.unsubscribe(self.comic_active)

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(subscription_count, 0)
        self.assertEqual(strip_count, 0)

    def test_unsubscribe_comic_active(self):
        """Should remove the subscription and the unread strip."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe(self.comic_active)

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 3)
        self.assertEqual(strip_count, 3)
        self.assertListEqual(
            comics, [self.comic_ended, self.comic_inactive, self.comic_inactive_ended]
        )

    def test_unsubscribe_comic_ended(self):
        """Should remove the subscription and the unread strip."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe(self.comic_ended)

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 3)
        self.assertEqual(strip_count, 3)
        self.assertListEqual(
            comics, [self.comic_active, self.comic_inactive, self.comic_inactive_ended]
        )

    def test_unsubscribe_comic_inactive(self):
        """Should not change anything since the comic is inactive
        and should not be able to unsubscribe."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe(self.comic_inactive)

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 3)
        self.assertEqual(strip_count, 3)
        self.assertListEqual(
            comics,
            [
                self.comic_active,
                self.comic_ended,
                self.comic_inactive_ended,
            ],
        )

    def test_unsubscribe_comic_inactive_ended(self):
        """Should not change anything since the comic is inactive
        and should not be able to unsubscribe."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe(self.comic_inactive_ended)

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 3)
        self.assertEqual(strip_count, 3)
        self.assertListEqual(
            comics,
            [
                self.comic_active,
                self.comic_ended,
                self.comic_inactive,
            ],
        )

    def test_unsubscribe_comic_not_subscribed(self):
        """Should not change anything since the comic is not subscribed."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe(self.comic_active2)

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 4)
        self.assertEqual(strip_count, 4)
        self.assertListEqual(
            comics,
            [
                self.comic_active,
                self.comic_ended,
                self.comic_inactive,
                self.comic_inactive_ended,
            ],
        )

    # ##################################
    # #   Test User.unsubscribe_list   #
    # ##################################

    def test_unsubscribe_list_empty(self):
        """Should not change anything since the user has no subscriptions."""
        self.user.unsubscribe_list([])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(subscription_count, 0)
        self.assertEqual(strip_count, 0)

    def test_unsubscribe_list(self):
        """Should remove the subscriptions and unread strips."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe_list([self.comic_active.id, self.comic_ended.id])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 2)
        self.assertEqual(strip_count, 2)
        self.assertListEqual(comics, [self.comic_inactive, self.comic_inactive_ended])

    def test_unsubscribe_list_ended(self):
        """Should remove the subscriptions and unread strips."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe_list([self.comic_ended.id])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 3)
        self.assertEqual(strip_count, 3)
        self.assertListEqual(
            comics,
            [
                self.comic_active,
                self.comic_inactive,
                self.comic_inactive_ended,
            ],
        )

    def test_unsubscribe_list_inactive(self):
        """Should not change anything since the comic is inactive
        and should not be able to unsubscribe."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe_list([self.comic_inactive.id])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 3)
        self.assertEqual(strip_count, 3)
        self.assertListEqual(
            comics,
            [
                self.comic_active,
                self.comic_ended,
                self.comic_inactive_ended,
            ],
        )

    def test_unsubscribe_list_inactive_ended(self):
        """Should not change anything since the comic is inactive
        and should not be able to unsubscribe."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe_list([self.comic_inactive_ended.id])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 3)
        self.assertEqual(strip_count, 3)
        self.assertListEqual(
            comics,
            [
                self.comic_active,
                self.comic_ended,
                self.comic_inactive,
            ],
        )

    def test_unsubscribe_list_not_subscribed(self):
        """Should not change anything since the comic is not subscribed."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe_list([self.comic_active2.id])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 4)
        self.assertEqual(strip_count, 4)
        self.assertListEqual(
            comics,
            [
                self.comic_active,
                self.comic_ended,
                self.comic_inactive,
                self.comic_inactive_ended,
            ],
        )

    def test_unsubscribe_list_duplicates(self):
        """Should remove the subscriptions and unread strips."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe_list(
            [self.comic_active.id, self.comic_ended.id, self.comic_active.id]
        )

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 2)
        self.assertEqual(strip_count, 2)
        self.assertListEqual(comics, [self.comic_inactive, self.comic_inactive_ended])

    def test_unsubscribe_list_mixed(self):
        """Should remove the subscriptions and unread strips."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe_list(
            [
                self.comic_active.id,
                self.comic_ended.id,
                self.comic_inactive.id,
                self.comic_inactive_ended.id,
                self.comic_active2.id,
            ]
        )

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 0)
        self.assertEqual(strip_count, 0)
        self.assertListEqual(comics, [])

    # #################################
    # #   Test User.unsubscribe_all   #
    # #################################

    def test_unsubscribe_all_empty(self):
        """Should not change anything since the user has no subscriptions."""
        self.user.unsubscribe_all()

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(subscription_count, 0)
        self.assertEqual(strip_count, 0)

    def test_unsubscribe_all(self):
        """Should remove all subscriptions and unread strips."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe_all()

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(subscription_count, 0)
        self.assertEqual(strip_count, 0)

    # #############################
    # #   Test User.mark_unread   #
    # #############################

    def test_mark_unread_empty(self):
        """Should not change anything since the user is not subscribed."""
        self.user.mark_unread(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_unread_not_subscribed(self):
        """Should not change anything since the user is not subscribed."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_unread(self.comic_active2)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 4)

    def test_mark_unread(self):
        """Should mark the comic as unread."""
        self.add_subscriptions()

        self.user.mark_unread(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 1)

    def test_mark_unread_ended(self):
        """Should mark the comic as unread."""
        self.add_subscriptions()

        self.user.mark_unread(self.comic_ended)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 1)

    def test_mark_unread_inactive(self):
        """Should not change anything since the comic is inactive."""
        self.add_subscriptions()

        self.user.mark_unread(self.comic_inactive)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_unread_inactive_ended(self):
        """Should not change anything since the comic is inactive and ended."""
        self.add_subscriptions()

        self.user.mark_unread(self.comic_inactive_ended)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_unread_already_unread(self):
        """Should mark the comic as unread."""
        self.add_subscriptions()
        self.user.unreadstrip_set.create(
            comic=self.comic_active, strip=self.strip_active
        )

        self.user.mark_unread(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 1)

    # ###########################
    # #   Test User.mark_read   #
    # ###########################

    def test_mark_read_empty(self):
        """Should not change anything since the user is not subscribed."""
        self.user.mark_read(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_read_not_subscribed(self):
        """Should not change anything since the user is not subscribed."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read(self.comic_active2)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 4)

    def test_mark_read(self):
        """Should mark the comic as read."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 3)

    def test_mark_read_ended(self):
        """Should mark the comic as read."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read(self.comic_ended)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 3)

    def test_mark_read_inactive(self):
        """Should not change anything since the comic is inactive."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read(self.comic_inactive)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 4)

    def test_mark_read_inactive_ended(self):
        """Should not change anything since the comic is inactive and ended."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read(self.comic_inactive_ended)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 4)

    def test_mark_read_already_read(self):
        """Should not change anything since the comic is already read."""
        self.add_subscriptions()

        self.user.mark_read(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_read_vote_positive(self):
        """Should add a positive vote to the comic."""
        self.add_subscriptions()
        self.add_unread_strips()
        old_comic = Comic.objects.get(pk=self.comic_active.id)

        self.user.mark_read(self.comic_active, 1)

        updated_comic = Comic.objects.get(pk=self.comic_active.id)

        self.assertEqual(updated_comic.total_votes, old_comic.total_votes + 1)
        self.assertEqual(updated_comic.positive_votes, old_comic.positive_votes + 1)

    def test_mark_read_vote_negative(self):
        """Should add a negative vote to the comic."""
        self.add_subscriptions()
        self.add_unread_strips()
        old_comic = Comic.objects.get(pk=self.comic_active.id)

        self.user.mark_read(self.comic_active, -1)

        updated_comic = Comic.objects.get(pk=self.comic_active.id)

        self.assertEqual(updated_comic.total_votes, old_comic.total_votes + 1)
        self.assertEqual(updated_comic.positive_votes, old_comic.positive_votes)

    def test_mark_read_vote_zero(self):
        """Should not add any votes to the comic."""
        self.add_subscriptions()
        self.add_unread_strips()
        old_comic = Comic.objects.get(pk=self.comic_active.id)

        self.user.mark_read(self.comic_active, 0)

        updated_comic = Comic.objects.get(pk=self.comic_active.id)

        self.assertEqual(updated_comic.total_votes, old_comic.total_votes)
        self.assertEqual(updated_comic.positive_votes, old_comic.positive_votes)

    # ###############################
    # #   Test User.mark_read_all   #
    # ###############################

    def test_mark_read_all_empty(self):
        """Should not change anything since the user is not subscribed."""
        self.user.mark_read_all()

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_read_all(self):
        """Should mark all comics as read."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read_all()

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_read_all_already_read(self):
        """Should not change anything since all comics are already read."""
        self.add_subscriptions()

        self.user.mark_read_all()

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_read_all_mixed(self):
        """Should mark all comics as read."""
        self.add_subscriptions()
        self.add_unread_strips()
        self.user.mark_read(self.comic_active)

        self.user.mark_read_all()

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

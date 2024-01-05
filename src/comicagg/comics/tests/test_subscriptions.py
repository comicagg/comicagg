from django.test import TestCase

from comicagg.accounts.models import IncompleteListError, InvalidComicError, User
from comicagg.comics.models import Comic, Subscription


class SubscriptionsTestCase(TestCase):
    fixtures = ["users.json", "comics.json", "strips.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.comic_active = Comic.objects.get(name="Active")
        self.comic_active2 = Comic.objects.get(name="Active2")
        self.comic_ended = Comic.objects.get(name="Ended")
        self.comic_inactive = Comic.objects.get(name="Inactive")
        self.comic_broken = Comic.objects.get(name="Broken")
        self.strip_active = self.comic_active.strip_set.first()
        self.strip_ended = self.comic_ended.strip_set.first()
        self.strip_inactive = self.comic_inactive.strip_set.first()
        self.strip_broken = self.comic_broken.strip_set.first()
        # Set up a second user
        self.user2 = User.objects.get(pk=2)
        self.user2.subscription_set.create(comic=self.comic_active, position=1)
        self.user2.subscription_set.create(comic=self.comic_ended, position=2)
        self.user2.subscription_set.create(comic=self.comic_inactive, position=3)
        self.user2.subscription_set.create(comic=self.comic_broken, position=4)

    def add_subscriptions(self):
        self.user.subscription_set.create(comic=self.comic_active, position=1)
        self.user.subscription_set.create(comic=self.comic_ended, position=2)
        self.user.subscription_set.create(comic=self.comic_inactive, position=3)
        self.user.subscription_set.create(comic=self.comic_broken, position=4)

    def add_unread_strips(self):
        self.user.unreadstrip_set.create(
            comic=self.comic_active, strip=self.strip_active
        )
        self.user.unreadstrip_set.create(comic=self.comic_ended, strip=self.strip_ended)
        self.user.unreadstrip_set.create(
            comic=self.comic_inactive, strip=self.strip_inactive
        )
        self.user.unreadstrip_set.create(
            comic=self.comic_broken, strip=self.strip_broken
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
        """Should return active, ended and broken comics."""
        self.add_subscriptions()

        all_subscriptions = self.user.subscriptions().count()

        self.assertEqual(all_subscriptions, 3)

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

        self.assertEqual(len(comics), 3)
        self.assertIsInstance(comics[0], Comic)
        self.assertListEqual(
            comics, [self.comic_active, self.comic_broken, self.comic_ended]
        )

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
        broken = self.user.is_subscribed(self.comic_broken)

        self.assertTrue(active)
        self.assertTrue(ended)
        self.assertTrue(broken)
        self.assertFalse(inactive)

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
        self.user.subscription_set.create(comic=self.comic_active, position=1)
        self.user.subscribe(self.comic_ended)

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 2)
        self.assertEqual(strip_count, 1)
        self.assertListEqual(comics, [self.comic_active, self.comic_ended])

    def test_subscribe_comic_broken(self):
        self.user.subscription_set.create(comic=self.comic_active, position=1)
        self.user.subscribe(self.comic_broken)

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 2)
        self.assertEqual(strip_count, 1)
        self.assertListEqual(comics, [self.comic_active, self.comic_broken])

    def test_subscribe_comic_inactive(self):
        with self.assertRaises(
            InvalidComicError, msg="Cannot subscribe to inactive comics"
        ):
            self.user.subscribe(self.comic_inactive)

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
        """Should create subscriptions for ended comics."""
        self.user.subscribe_list([self.comic_ended.id])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(subscription_count, 1)
        self.assertEqual(strip_count, 1)

    def test_subscribe_list_broken(self):
        """Should not create subscriptions for inactive and ended comics."""
        self.user.subscribe_list([self.comic_broken.id])

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(subscription_count, 1)
        self.assertEqual(strip_count, 1)

    def test_subscribe_list_inactive(self):
        """Should not create subscriptions for inactive comics."""
        self.user.subscribe_list([self.comic_inactive.id])

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
        """Should not create subscriptions for inactive comics."""
        self.user.subscribe_list(
            [
                self.comic_active.id,
                self.comic_ended.id,
                self.comic_broken.id,
                self.comic_inactive.id,
                self.comic_active2.id,
            ]
        )

        subscription_count = self.user.subscription_set.count()
        strip_count = self.user.unreadstrip_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 4)
        self.assertEqual(strip_count, 3)
        self.assertListEqual(
            comics,
            [
                self.comic_active,
                self.comic_ended,
                self.comic_broken,
                self.comic_active2,
            ],
        )

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
            comics, [self.comic_ended, self.comic_inactive, self.comic_broken]
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
            comics, [self.comic_active, self.comic_inactive, self.comic_broken]
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
                self.comic_broken,
            ],
        )

    def test_unsubscribe_comic_inactive_ended(self):
        """Should not change anything since the comic is inactive
        and should not be able to unsubscribe."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe(self.comic_broken)

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
                self.comic_broken,
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
        self.assertListEqual(comics, [self.comic_inactive, self.comic_broken])

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
                self.comic_broken,
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
                self.comic_broken,
            ],
        )

    def test_unsubscribe_list_inactive_ended(self):
        """Should not change anything since the comic is inactive
        and should not be able to unsubscribe."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe_list([self.comic_broken.id])

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
                self.comic_broken,
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
        self.assertListEqual(comics, [self.comic_inactive, self.comic_broken])

    def test_unsubscribe_list_mixed(self):
        """Should remove the subscriptions and unread strips."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.unsubscribe_list(
            [
                self.comic_active.id,
                self.comic_ended.id,
                self.comic_inactive.id,
                self.comic_broken.id,
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

    # #######################################
    # #   Test User.subscriptions_reorder   #
    # #######################################

    # The method receives a list of comic ids and reorders the subscriptions in that order.
    # The list must contain all the subscriptions, otherwise an exception is raised.
    # The list can contain duplicates, but they are ignored.
    # The list cannot contain comics that are not subscribed or an exception will be raised.

    def test_subscriptions_reorder_empty(self):
        """Should not change anything since the user has no subscriptions."""
        self.user.subscriptions_reorder([])

        subscription_count = self.user.subscription_set.count()
        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]

        self.assertEqual(subscription_count, 0)
        self.assertListEqual(comics, [])

    def test_subscriptions_reorder_incomplete(self):
        """Should raise an exception since there are more subscriptions in the database
        than in the call."""
        self.add_subscriptions()

        with self.assertRaises(IncompleteListError):
            self.user.subscriptions_reorder(
                [self.comic_active.id, self.comic_inactive.id]
            )

    def test_subscriptions_reorder(self):
        """Should reorder the subscriptions."""
        self.add_subscriptions()

        self.user.subscriptions_reorder(
            [
                self.comic_broken.id,
                self.comic_active.id,
                self.comic_inactive.id,
                self.comic_ended.id,
            ]
        )

        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]
        first_subscription: Subscription = self.user.subscription_set.all()[0]

        self.assertListEqual(
            comics,
            [
                self.comic_broken,
                self.comic_active,
                self.comic_inactive,
                self.comic_ended,
            ],
        )
        self.assertEqual(first_subscription.position, 1)

    def test_subscriptions_reorder_duplicates(self):
        """Should reorder the subscriptions."""
        self.add_subscriptions()

        self.user.subscriptions_reorder(
            [
                self.comic_broken.id,
                self.comic_active.id,
                self.comic_inactive.id,
                self.comic_ended.id,
                self.comic_active.id,
            ]
        )

        comics = [
            subscription.comic for subscription in self.user.subscription_set.all()
        ]
        first_subscription: Subscription = self.user.subscription_set.all()[0]

        self.assertListEqual(
            comics,
            [
                self.comic_broken,
                self.comic_active,
                self.comic_inactive,
                self.comic_ended,
            ],
        )
        self.assertEqual(first_subscription.position, 1)

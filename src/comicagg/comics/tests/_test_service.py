"""Tests that target the AggregatorService class"""
from django.contrib.auth.models import User
from django.test import TestCase

from comicagg.comics.models import Comic, Strip, UnreadStrip
from comicagg.comics.services import AggregatorService


class SubscriptionTests(TestCase):
    fixtures = ["comics.json", "strips.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="test_user", email="test_user@tests.dev", password="top_secret"
        )
        self.aggregator = AggregatorService(self.user)

    # Tests for AggregatorService.subscribed_all()
    def test_all_comics_empty(self):
        """Test that the user is not subscribed to any comic."""
        self.assertEqual(len(self.aggregator.subscribed_all()), 0)
        self.assertEqual(self.aggregator.unread_strips_count(), 0)

    def test_all_comics(self):
        """Test that the returned list contains 3 items."""
        self.assertEqual(len(self.aggregator.subscribed_all()), 0)
        comic_ended = Comic.objects.get(pk=1)
        self.aggregator.subscribe_comic(comic_ended)
        comic_active = Comic.objects.get(pk=2)
        self.aggregator.subscribe_comic(comic_active)
        comic_disabled = Comic.objects.get(pk=9)
        self.aggregator.subscribe_comic(comic_disabled)

        all_comics = self.aggregator.subscribed_all()
        self.assertEqual(len(all_comics), 3)

    # Tests for AggregatorService.subscribed_comics()
    def test_filtered_comics_empty(self):
        """Test that the user is not subscribed to any comic."""
        self.assertEqual(len(self.aggregator.subscribed_all()), 0)
        filtered = self.aggregator.subscribed_comics()
        self.assertEqual(len(filtered), 0)

    def test_filtered_comics(self):
        """Test that the returned list contains 2 items."""
        self.assertEqual(len(self.aggregator.subscribed_all()), 0)
        comic_ended = Comic.objects.get(pk=1)
        self.aggregator.subscribe_comic(comic_ended)
        comic_active = Comic.objects.get(pk=2)
        self.aggregator.subscribe_comic(comic_active)
        comic_disabled = Comic.objects.get(pk=9)
        self.aggregator.subscribe_comic(comic_disabled)

        filtered = self.aggregator.subscribed_comics()
        self.assertEqual(len(filtered), 2)

    # Tests for AggregatorService.random_comic()
    def test_random_comic_none(self):
        """Test that no random comic is available if the user is subscribed to all the comics.

        Subscribe the user to all the comics so there cannot be any random suggestion
        NOTE: Is this test is actually contained in the next one?"""
        self.assertEqual(len(self.aggregator.subscribed_all()), 0)
        comics = Comic.objects.all()
        comics_idx = [comic.id for comic in comics]
        self.aggregator.subscribe_comics(comics_idx)
        self.assertEqual(len(self.aggregator.subscribed_all()), comics.count())

        random = self.aggregator.random_comic()
        self.assertIsNone(random)

    def test_random_comic(self):
        """Test that a random comic must be active and not ended.

        We subscribe the user to all the active comics, so that no random comic
        can be suggested.
        """
        self.assertEqual(len(self.aggregator.subscribed_all()), 0)
        comics = Comic.objects.available()
        comics_idx = [comic.id for comic in comics]
        self.aggregator.subscribe_comics(comics_idx)
        self.assertEqual(len(self.aggregator.subscribed_all()), comics.count())

        random_strip = self.aggregator.random_comic()
        self.assertIsNone(random_strip)

    def test_random_comic_one(self):
        """Test that a random comic must be active and not ended.

        We subscribe the user to all the active comics but one and confirm that
        this is the random comic suggested.
        Also, the comic strip returned must be the most recent.
        We need to make sure that the suggested is the Comic with ID 7,
        because it's the one with several strips in the fixtures.
        """
        suggested_id = 7
        self.assertEqual(len(self.aggregator.subscribed_all()), 0)
        comics = Comic.objects.available()
        comics_idx = [comic.id for comic in comics]
        comics_idx.remove(suggested_id)
        suggested_comic = comics.filter(id=suggested_id).first()
        self.aggregator.subscribe_comics(comics_idx)
        self.assertEqual(len(self.aggregator.subscribed_all()), len(comics_idx))

        random_strip = self.aggregator.random_comic()
        self.assertIsNotNone(random_strip)
        self.assertTrue(random_strip.comic.active)
        self.assertFalse(random_strip.comic.ended)
        self.assertEqual(random_strip.comic.id, suggested_id)
        self.assertEqual(random_strip.url, suggested_comic.last_strip.url)

    # Tests for AggregatorService.is_subscribed(comic)
    def test_is_subscribed(self):
        """Test that the user is subscribed to a comic."""
        self.assertEqual(len(self.aggregator.subscribed_all()), 0)
        comic = Comic.objects.get(pk=1)
        # We know that the user cannot be subscribed now to the comic.
        self.assertFalse(self.aggregator.is_subscribed(comic))

        self.aggregator.subscribe_comic(comic)
        self.assertTrue(self.aggregator.is_subscribed(comic))
        self.assertEqual(len(self.aggregator.subscribed_all()), 1)
        # If we subscribe the user again, it shouldn't change anything
        self.aggregator.subscribe_comic(comic)
        self.assertTrue(self.aggregator.is_subscribed(comic))
        self.assertEqual(len(self.aggregator.subscribed_all()), 1)

    # Tests for AggregatorService.subscribe_comic(comic)
    def test_subscribe_comic(self):
        """Test what happens when a user subscribes to one comic with strips and without strips."""
        self.assertEqual(len(self.aggregator.subscribed_all()), 0)
        self.assertEqual(self.aggregator.unread_strips_count(), 0)
        comic_with = Comic.objects.get(pk=1)
        comic_without = Comic.objects.get(pk=3)

        # Subscribe to a comic with one strip, user should end up with one comic and one unread
        # TODO: We should test also with a comic marked as new, but there are no fixtures with new comics yet
        self.aggregator.subscribe_comic(comic_with)
        self.assertEqual(len(self.aggregator.subscribed_all()), 1)
        self.assertEqual(self.aggregator.unread_strips_count(), 1)

        # Subscribe to the same comic again, no changes should have happened
        self.aggregator.subscribe_comic(comic_with)
        self.assertEqual(len(self.aggregator.subscribed_all()), 1)
        self.assertEqual(self.aggregator.unread_strips_count(), 1)

        # Subscribe to a comic without strips, two subscribed comics but just one unread.
        self.aggregator.subscribe_comic(comic_without)
        self.assertEqual(len(self.aggregator.subscribed_all()), 2)
        self.assertEqual(self.aggregator.unread_strips_count(), 1)

    # Tests for AggregatorService.subscribe_comics(id_list)
    # Tests for AggregatorService.unsubscribe_comic(comic)
    # Tests for AggregatorService.unsubscribe_comics(id_list)
    # Tests for AggregatorService.unsubscribe_all_comics()


class UnreadTests(TestCase):
    fixtures = ["comics.json", "strips.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="test_user", email="test_user@tests.dev", password="top_secret"
        )
        self.aggregator = AggregatorService(self.user)
        self.comic_active = Comic.objects.get(pk=2)
        self.comic_ended = Comic.objects.get(pk=1)
        self.comic_inactive = Comic.objects.get(pk=9)

    # Tests for AggregatorService.unread_strips()
    def test_unread_strips_positive(self):
        """Test that the user has an expected number of unread strips."""
        # Arrange
        strip_active = self.comic_active.strip_set.first()
        strip_inactive = self.comic_inactive.strip_set.first()
        strip_ended = self.comic_ended.strip_set.first()
        UnreadStrip.objects.create(
            user=self.user, comic=self.comic_active, strip=strip_active
        )
        UnreadStrip.objects.create(
            user=self.user, comic=self.comic_inactive, strip=strip_inactive
        )
        UnreadStrip.objects.create(
            user=self.user, comic=self.comic_ended, strip=strip_ended
        )
        # Act
        unread_strips = self.aggregator.unread_strips()
        unread_comics = self.aggregator.unread_comics()
        # Assert
        self.assertEqual(len(unread_strips), 0)
        self.assertEqual(len(unread_comics), 0)

    def test_unread_strips_empty(self):
        """Test that the user does not have any unread strips."""
        # Arrange
        strip_inactive = self.comic_inactive.strip_set.first()
        UnreadStrip.objects.create(
            user=self.user, comic=self.comic_inactive, strip=strip_inactive
        )
        # Act
        unread_strips = self.aggregator.unread_strips()
        unread_comics = self.aggregator.unread_comics()
        # Assert
        self.assertEqual(len(unread_strips), 0)
        self.assertEqual(len(unread_comics), 0)

"""Tests that target the UserOperations class"""
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from comicagg.comics.utils import UserOperations
from comicagg.comics.models import Comic, active_comics

class SubscriptionTests(TestCase):
    fixtures = ['comics.json', 'comichistory.json']

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='test_user', email='test_user@tests.dev', password='top_secret')
        self.operations = UserOperations(self.user)

    # Tests for UserOperations.subscribed_all()
    def test_all_comics_empty(self):
        """Test that the user is not subscribed to any comic."""
        self.assertEqual(len(self.operations.subscribed_all()), 0)
        self.assertEqual(self.operations.unread_strips_count(), 0)

    def test_all_comics(self):
        """Test that the returned list contains 3 items."""
        self.assertEqual(len(self.operations.subscribed_all()), 0)
        comic_ended= Comic.objects.get(pk=1)
        self.operations.subscribe_comic(comic_ended)
        comic_active = Comic.objects.get(pk=2)
        self.operations.subscribe_comic(comic_active)
        comic_disabled= Comic.objects.get(pk=9)
        self.operations.subscribe_comic(comic_disabled)

        all_comics = self.operations.subscribed_all()
        self.assertEqual(len(all_comics), 3)

    # Tests for UserOperations.subscribed_comics()
    def test_filtered_comics_empty(self):
        """Test that the user is not subscribed to any comic."""
        self.assertEqual(len(self.operations.subscribed_all()), 0)
        filtered = self.operations.subscribed_comics()
        self.assertEqual(len(filtered), 0)

    def test_filtered_comics(self):
        """Test that the returned list contains 2 items."""
        self.assertEqual(len(self.operations.subscribed_all()), 0)
        comic_ended= Comic.objects.get(pk=1)
        self.operations.subscribe_comic(comic_ended)
        comic_active = Comic.objects.get(pk=2)
        self.operations.subscribe_comic(comic_active)
        comic_disabled= Comic.objects.get(pk=9)
        self.operations.subscribe_comic(comic_disabled)

        filtered = self.operations.subscribed_comics()
        self.assertEqual(len(filtered), 2)

    # Tests for UserOperations.random_comic()
    def test_random_comic_none(self):
        """Test that no random comic is available if the user is subscribed to all the comics.

        Subscribe the user to all the comics so there cannot be any random suggestion
        NOTE: Is this test is actually contained in the next one?"""
        self.assertEqual(len(self.operations.subscribed_all()), 0)
        comics = Comic.objects.all()
        comics_idx = [comic.id for comic in comics]
        self.operations.subscribe_comics(comics_idx)
        self.assertEqual(len(self.operations.subscribed_all()), comics.count())

        random = self.operations.random_comic()
        self.assertIsNone(random)

    def test_random_comic(self):
        """Test that a random comic must be active and not ended.

        We subscribe the user to all the active comics, so that no random comic can be suggested.
        """
        self.assertEqual(len(self.operations.subscribed_all()), 0)
        comics = active_comics()
        comics_idx = [comic.id for comic in comics]
        self.operations.subscribe_comics(comics_idx)
        self.assertEqual(len(self.operations.subscribed_all()), comics.count())

        random_history = self.operations.random_comic()
        self.assertIsNone(random_history)

    def test_random_comic_one(self):
        """Test that a random comic must be active and not ended.

        We subscribe the user to all the active comics but one and we confirm that that is the random comic suggested.
        Also, the comic history returned must be the most recent.
        We need to make sure that the suggested is the Comic with ID 7, because it's the one with several strips in the fixtures.
        """
        suggested_id = 7
        self.assertEqual(len(self.operations.subscribed_all()), 0)
        comics = active_comics()
        comics_idx = [comic.id for comic in comics]
        comics_idx.remove(suggested_id)
        suggested_comic = comics.filter(id=suggested_id).first()
        self.operations.subscribe_comics(comics_idx)
        self.assertEqual(len(self.operations.subscribed_all()), len(comics_idx))

        random_history = self.operations.random_comic()
        self.assertIsNotNone(random_history)
        self.assertTrue(random_history.comic.activo)
        self.assertFalse(random_history.comic.ended)
        self.assertEqual(random_history.comic.id, suggested_id)
        self.assertEqual(random_history.url, suggested_comic.last_strip().url)

    # Tests for UserOperations.is_subscribed(comic)
    def test_is_subscribed(self):
        """Test that the user is subscribed to a comic."""
        self.assertEqual(len(self.operations.subscribed_all()), 0)
        comic = Comic.objects.get(pk=1)
        # We know that the user cannot be subscribed now to the comic.
        self.assertFalse(self.operations.is_subscribed(comic))

        self.operations.subscribe_comic(comic)
        self.assertTrue(self.operations.is_subscribed(comic))
        self.assertEqual(len(self.operations.subscribed_all()), 1)
        # If we subscribe the user again, it shouldn't change anything
        self.operations.subscribe_comic(comic)
        self.assertTrue(self.operations.is_subscribed(comic))
        self.assertEqual(len(self.operations.subscribed_all()), 1)

    # Tests for UserOperations.subscribe_comic(comic)
    def test_subscribe_comic(self):
        """Test what happens when a user subscribes to one comic with strips and without strips."""
        self.assertEqual(len(self.operations.subscribed_all()), 0)
        self.assertEqual(self.operations.unread_strips_count(), 0)
        comic_with = Comic.objects.get(pk=1)
        comic_without = Comic.objects.get(pk=3)

        # Subscribe to a comic with one strip, user should end up with one comic and one unread
        # TODO: We should test also with a comic marked as new, but there are no fixtures with new comics yet
        self.operations.subscribe_comic(comic_with)
        self.assertEqual(len(self.operations.subscribed_all()), 1)
        self.assertEqual(self.operations.unread_strips_count(), 1)

        # Subscribe to the same comic again, no changes should have happened
        self.operations.subscribe_comic(comic_with)
        self.assertEqual(len(self.operations.subscribed_all()), 1)
        self.assertEqual(self.operations.unread_strips_count(), 1)

        # Subscribe to a comic without strips, two subscribed comics but just one unread.
        self.operations.subscribe_comic(comic_without)
        self.assertEqual(len(self.operations.subscribed_all()), 2)
        self.assertEqual(self.operations.unread_strips_count(), 1)

    # Tests for UserOperations.subscribe_comics(id_list)
    # Tests for UserOperations.unsubscribe_comic(comic)
    # Tests for UserOperations.unsubscribe_comics(id_list)
    # Tests for UserOperations.unsubscribe_all_comics()

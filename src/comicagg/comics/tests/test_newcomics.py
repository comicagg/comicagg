from django.test import TestCase

from comicagg.accounts.models import User
from comicagg.comics.models import Comic, NewComic, UnreadStrip


class NewComicTestCase(TestCase):
    fixtures = ["users.json", "comics.json", "strips.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.comic_active = Comic.objects.get(name="Active")
        self.comic_ended = Comic.objects.get(name="Ended")
        self.comic_inactive = Comic.objects.get(name="Inactive")
        self.comic_inactive_ended = Comic.objects.get(name="InactiveEnded")

    # ############################
    # #   Test User.comics_new   #
    # ############################

    def test_comics_new_empty(self):
        """No new comics."""
        new_comics = self.user.comics_new()

        self.assertEqual(len(new_comics), 0)

    def test_comics_new_active(self):
        """Should return one active new comic."""
        NewComic.objects.create(user=self.user, comic=self.comic_active)

        new_comics = self.user.comics_new()

        self.assertEqual(len(new_comics), 1)

    def test_comics_new_ended(self):
        """Should return one ended new comic."""
        NewComic.objects.create(user=self.user, comic=self.comic_ended)

        new_comics = self.user.comics_new()

        self.assertEqual(len(new_comics), 1)

    def test_comics_new_inactive(self):
        """Should return no new comics."""
        NewComic.objects.create(user=self.user, comic=self.comic_inactive)

        new_comics = self.user.comics_new()

        self.assertEqual(len(new_comics), 0)

    def test_comics_new_inactive_ended(self):
        """Should return no new comics."""
        NewComic.objects.create(user=self.user, comic=self.comic_inactive_ended)

        new_comics = self.user.comics_new()

        self.assertEqual(len(new_comics), 0)

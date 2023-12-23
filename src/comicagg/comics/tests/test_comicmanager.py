from django.test import TestCase
from comicagg.accounts.models import User

from comicagg.comics.models import Comic, Subscription

from comicagg.comics.managers import ComicManager


class ComicManagerTestCase(TestCase):
    fixtures = ["comics.json"]

    def setUp(self):
        self.comic_active = Comic.objects.get(name="Active")
        self.comic_ended = Comic.objects.get(name="Ended")
        self.comic_inactive = Comic.objects.get(name="Inactive")
        self.comic_inactive_ended = Comic.objects.get(name="InactiveEnded")

    # ###################################
    # #   Test ComicManager.available   #
    # ###################################

    def test_comicmanager_available_all(self):
        comics = Comic.objects.available()

        self.assertEqual(comics.count(), 3)

    def test_comicmanager_available_active(self):
        comics = Comic.objects.available(include_ended=False)

        self.assertEqual(comics.count(), 2)

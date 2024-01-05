from django.test import TestCase

from comicagg.comics.models import Comic


class ComicManagerTestCase(TestCase):
    fixtures = ["comics.json"]

    def setUp(self):
        pass

    # ###################################
    # #   Test ComicManager.available   #
    # ###################################

    def test_comicmanager_available_all(self):
        comics = Comic.objects.available()

        self.assertEqual(comics.count(), 4)

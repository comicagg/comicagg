from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from comicagg.comics.utils import UserOperations
from comicagg.comics.models import Comic

"""
Comics in the fixtures

ID  Ended   Active  Status
1   True    False   Ended
2   False   True    Active
9   False   False   Disabled
"""

class SubscriptionTests(TestCase):
    fixtures = ['comics.json', 'comichistory.json']

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='test_user', email='test_user@tests.dev', password='top_secret')
        self.operations = UserOperations(self.user)

    def test_all_comics_empty(self):
        """Test for UserOperations.subscribed_all()."""
        all_comics = self.operations.subscribed_all()
        self.assertEqual(len(all_comics), 0)

    def test_all_comics(self):
        """Test for UserOperations.subscribed_all()."""
        comic_ended= Comic.objects.get(pk=1)
        self.operations.subscribe_comic(comic_ended)
        comic_active = Comic.objects.get(pk=2)
        self.operations.subscribe_comic(comic_active)
        comic_disabled= Comic.objects.get(pk=9)
        self.operations.subscribe_comic(comic_disabled)

        all_comics = self.operations.subscribed_all()
        self.assertEqual(len(all_comics), 3)

    def test_filtered_comics_empty(self):
        """Test for UserOperations.subscribed_comics()."""
        filtered = self.operations.subscribed_comics()
        self.assertEqual(len(filtered), 0)

    def test_filtered_comics(self):
        """Test for UserOperations.subscribed_comics()."""
        comic_ended= Comic.objects.get(pk=1)
        self.operations.subscribe_comic(comic_ended)
        comic_active = Comic.objects.get(pk=2)
        self.operations.subscribe_comic(comic_active)
        comic_disabled= Comic.objects.get(pk=9)
        self.operations.subscribe_comic(comic_disabled)

        filtered = self.operations.subscribed_comics()
        self.assertEqual(len(filtered), 2)
        
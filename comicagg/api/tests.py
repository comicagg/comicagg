"""Test suite for HTTP request to the API."""
import json
import xml.etree.ElementTree as ET
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.utils.encoding import smart_text
from comicagg.comics.models import Comic
from comicagg.comics.utils import UserOperations

test_user = 'test'
test_pwd = 'pwd'

"""
Comics in the fixtures

ID  Ended   Active  Status
1   True    False   Ended
2   False   True    Active
9   False   False   Disabled
"""

class ErrorTests(TestCase):
    """Tests that should trigget HTTP error codes."""

    def setUp(self):
        pass

    def test_anon_get_index(self):
        """ Anonymous request that should get a 401 """
        r = self.client.get('/api/')
        self.assertEqual(r.status_code, 401)

class IndexTests(TestCase):
    """Tests for the Index view."""

    fixtures = ['comics.json', 'users.json']

    def setUp(self):
        login_ok = self.client.login(username=test_user, password=test_pwd)
        self.assertTrue(login_ok)

    def test_get(self):
        """Authenticated request should get a 200"""
        r = self.client.get('/api/')
        self.assertEqual(r.status_code, 200)

class SubscriptionTests(TestCase):
    """Tests for subscription related operations."""

    fixtures = ['comics.json', 'users.json']

    def setUp(self):
        login_ok = self.client.login(username=test_user, password=test_pwd)
        self.assertTrue(login_ok)

    def test_get_empty(self):
        """This get should return an empty subscriptions set."""
        response = self.client.get('/api/subscriptions')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(smart_text(response.content), '{"subscriptions":[]}')

    def test_get_empty_xml(self):
        """This get should return an empty subscriptions set."""
        response = self.client.get('/api/subscriptions', HTTP_ACCEPT='text/xml')
        self.assertEqual(response.status_code, 200)
        self.assertXMLEqual(smart_text(response.content), '<?xml version="1.0" encoding="UTF-8" ?><subscriptions></subscriptions>')

    def test_get_with_subscriptions(self):
        """This get should return a subscriptions set with 2 results."""
        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        operations.subscribe_comics([1, 2, 9])

        response = self.client.get('/api/subscriptions')
        self.assertEqual(response.status_code, 200)

        content = json.loads(smart_text(response.content))
        self.assertEqual('subscriptions' in content.keys(), True)
        self.assertEqual(len(content['subscriptions']), 2)

    def test_get_with_subscriptions_xml(self):
        """This get should return a subscriptions set with 2 results."""
        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        operations.subscribe_comics([1, 2, 9])

        response = self.client.get('/api/subscriptions', HTTP_ACCEPT='text/xml')
        self.assertEqual(response.status_code, 200)

        content = ET.fromstring(smart_text(response.content))
        self.assertEqual(content.tag, 'subscriptions')
        self.assertEqual(len(content.findall("comic")), 2)

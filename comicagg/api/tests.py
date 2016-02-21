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
        """An anonymous request should get a 401."""
        r = self.client.get('/api/')
        self.assertEqual(r.status_code, 401)

class IndexTests(TestCase):
    """Tests for the Index view."""

    fixtures = ['comics.json', 'users.json']

    def setUp(self):
        login_ok = self.client.login(username=test_user, password=test_pwd)
        self.assertTrue(login_ok)

    def test_get(self):
        """An authenticated request should get a 200."""
        r = self.client.get('/api/')
        self.assertEqual(r.status_code, 200)

class ComicTests(TestCase):
    pass
    #TODO: GET cases

class StripTests(TestCase):
    """Tests for strip related operations."""

    fixtures = ['comics.json', 'users.json', 'comichistory.json']

    def setUp(self):
        login_ok = self.client.login(username=test_user, password=test_pwd)
        self.assertTrue(login_ok)

    def test_get(self):
        """An authenticated request should get a 200."""
        r = self.client.get('/api/strips/1')
        self.assertEqual(r.status_code, 200)

    def test_put_subscribed(self):
        """An authenticated request should get a 200."""
        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        operations.subscribe_comics([7])

        r = self.client.put('/api/strips/1')
        self.assertEqual(r.status_code, 204)

    def test_put_unsubscribed(self):
        """An authenticated request should get a 200."""
        r = self.client.put('/api/strips/1')
        self.assertEqual(r.status_code, 400)

    #TODO: GET cases
    #TODO: PUT cases
    #TODO: DELETE cases

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

    #TODO: GET cases
    #TODO: POST cases
    #TODO: PUT cases
    #TODO: DELETE cases

class UnreadTests(TestCase):
    pass
    #TODO: GET cases
    #TODO: POST cases
    #TODO: PUT cases
    #TODO: DELETE cases

class UserTests(TestCase):
    pass
    #TODO: GET cases

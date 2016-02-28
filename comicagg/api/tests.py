"""Test suite for HTTP request to the API."""
import json
from urllib.parse import urlencode
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

class AnonTests(TestCase):
    """Anonymous requests tests."""

    def setUp(self):
        pass

    def test_anon(self):
        """An anonymous request should get a 401."""
        r = self.client.get('/api/')
        self.assertEqual(r.status_code, 401)

class LoggedInTestCase(TestCase):
    fixtures = ['users.json', 'comics.json', 'comichistory.json']

    def setUp(self):
        login_ok = self.client.login(username=test_user, password=test_pwd)
        self.assertTrue(login_ok)

class IndexTests(LoggedInTestCase):
    """Tests for the Index view."""

    def test_get(self):
        """An authenticated request should get a 200."""
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, 200)

class ComicTests(LoggedInTestCase):
    """Tests for comic related operations."""

    # GET cases
    def test_get_all(self):
        """Get all the comics, get a 200."""
        response = self.client.get('/api/comics')
        self.assertEqual(response.status_code, 200)
        j = response.json()
        # There are 5 active comics in the fixtures
        self.assertEqual(len(j['response']['comics']), 5)

    def test_get_one_active(self):
        """Get one comic that exists, get a 200."""
        response = self.client.get('/api/comics/2')
        self.assertEqual(response.status_code, 200)
        j = response.json()
        self.assertFalse(j['response']['comic']['ended'])

    def test_get_one_ended(self):
        """Get one comic that exists, get a 200."""
        response = self.client.get('/api/comics/1')
        self.assertEqual(response.status_code, 200)
        j = response.json()
        self.assertTrue(j['response']['comic']['ended'])

    def test_get_one_disabled(self):
        """Get one comic that exists but disabled, get a 404."""
        response = self.client.get('/api/comics/9')
        self.assertEqual(response.status_code, 404)

    def test_get_one_invalid(self):
        """Get one invalid comic, get a 404."""
        response = self.client.get('/api/comics/1000')
        self.assertEqual(response.status_code, 404)

        response = self.client.get('/api/comics/-1000')
        self.assertEqual(response.status_code, 404)

class SubscriptionTests(LoggedInTestCase):
    """Tests for subscription related operations."""

    # GET cases
    def test_get_empty(self):
        """This get should return an empty subscriptions set."""
        response = self.client.get('/api/subscriptions')
        self.assertEqual(response.status_code, 200)
        j = response.json()
        self.assertListEqual(j['response']['subscriptions'], list())

    def test_get_with_subscriptions(self):
        """This get should return a subscriptions set with 2 results."""
        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        operations.subscribe_comics([1, 2, 9])

        response = self.client.get('/api/subscriptions')
        self.assertEqual(response.status_code, 200)

        j = response.json()
        self.assertEqual(len(j['response']['subscriptions']), 2)

    # POST cases
    # Invalid bodies
    def test_post_wrong_body(self):
        """Send wrong bodies."""
        response = self.client.post('/api/subscriptions', '',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/api/subscriptions', 'subscribe',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/api/subscriptions', 'subscribe=',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/api/subscriptions', 'subscribe_me=',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/api/subscriptions', 'subscribe_me=1',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/api/subscriptions', 'subscribe_me=1,2',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

    # Subscribe to one
    def test_post_one_active(self):
        """Subscribe the user to one comic."""
        response = self.client.post('/api/subscriptions', 'subscribe=2',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        self.assertEqual(len(operations.subscribed_all()), 1)


    def test_post_one_ended(self):
        """Subscribe the user to one ended comic."""
        response = self.client.post('/api/subscriptions', 'subscribe=1',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        self.assertEqual(len(operations.subscribed_all()), 1)

    def test_post_one_disabled(self):
        """Subscribe the user to one disabled comic."""
        response = self.client.post('/api/subscriptions', 'subscribe=9',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

    # Subscribe to several
    def test_post_several(self):
        """Subscribe the user to several comics."""
        # 2 active, 2 ended
        response = self.client.post('/api/subscriptions', 'subscribe=1,3,2,4',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        self.assertEqual(len(operations.subscribed_all()), 4)

    # Subscribe to several with messed up but accepted values
    def test_post_format(self):
        """Subscribe the user to several comics."""
        response = self.client.post('/api/subscriptions', 'subscribe=1,3,,2,4',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        self.assertEqual(len(operations.subscribed_all()), 4)

    def test_post_format2(self):
        """Subscribe the user to several comics."""
        response = self.client.post('/api/subscriptions', 'subscribe=,1,,3,2,4',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        self.assertEqual(len(operations.subscribed_all()), 4)

    def test_post_duplicate(self):
        """Subscribe the user to several comics."""
        response = self.client.post('/api/subscriptions', 'subscribe=1,2,3,2,4',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        self.assertEqual(len(operations.subscribed_all()), 4)

    #PUT cases
    def test_put_wrong_body(self):
        """Send wrong bodies."""
        response = self.client.put('/api/subscriptions', '',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

        response = self.client.put('/api/subscriptions', 'subscriptionsz',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

    def test_put_none(self):
        """Remove all user subscriptions and get a 204."""
        response = self.client.put('/api/subscriptions','subscriptions=',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 204)

        response = self.client.put('/api/subscriptions', 'subscriptions',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

    # TODO test cases with already subscribed comics to test order and added/removed
    def test_put_one(self):
        """Subscribe to one comic."""
        response = self.client.put('/api/subscriptions', 'subscriptions=1',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 204)

        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        self.assertEqual(len(operations.subscribed_all()), 1)

    def test_put_several(self):
        """We will subscribe the user to several comics and we should get a 204."""
        response = self.client.put('/api/subscriptions', 'subscriptions=1,3,2,4',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 204)

        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        self.assertEqual(len(operations.subscribed_all()), 4)

    # DELETE cases
    def test_delete_empty(self):
        """Remove all subscriptions."""
        response = self.client.delete('/api/subscriptions')
        self.assertEqual(response.status_code, 200)

    def test_delete_with(self):
        """Remove all subscriptions."""
        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        operations.subscribe_comics([1, 2, 3, 4])

        response = self.client.delete('/api/subscriptions')
        self.assertEqual(response.status_code, 200)

        j = response.json()
        self.assertEqual(j['response']['removed_subscriptions'], [1, 2, 3, 4])
        self.assertEqual(len(operations.subscribed_all()), 0)

# TODO
class UnreadTests(LoggedInTestCase):
    """Tests for unread comics related operations."""

    def test_get_all(self):
        """Get info of all the comics, get a 200."""
        r = self.client.get('/api/unreads')
        self.assertEqual(r.status_code, 200)

    def test_get_one(self):
        """Get info of all the comics, get a 200."""
        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        operations.subscribe_comics([1])

        r = self.client.get('/api/unreads/1')
        self.assertEqual(r.status_code, 200)

    def test_get_one_invalid(self):
        """Get info of all the comics, get a 200."""
        r = self.client.get('/api/unreads/100')
        self.assertEqual(r.status_code, 404)
    #TODO: GET cases

    def test_post_all(self):
        """Get info of all the comics, get a 200."""
        r = self.client.post('/api/unreads')
        self.assertEqual(r.status_code, 405)

    def test_post_one(self):
        """Get info of all the comics, get a 200."""
        r = self.client.post('/api/unreads/1')
        self.assertEqual(r.status_code, 204)

    def test_post_one_invalid(self):
        """Get info of all the comics, get a 200."""
        r = self.client.post('/api/unreads/100')
        self.assertEqual(r.status_code, 404)
    #TODO: POST cases

    def test_put_all(self):
        """Get info of all the comics, get a 200."""
        r = self.client.put('/api/unreads')
        self.assertEqual(r.status_code, 405)

    def test_put_ok(self):
        """Get info of all the comics, get a 200."""
        r = self.client.put('/api/unreads/1', 'vote=1',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 204)

    def test_put_invalid_comic(self):
        """Get info of all the comics, get a 200."""
        r = self.client.put('/api/unreads/100', 'vote=1',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 404)

    def test_put_invalid_vote(self):
        """Get info of all the comics, get a 200."""
        r = self.client.put('/api/unreads/1')
        self.assertEqual(r.status_code, 400)
        r = self.client.put('/api/unreads/1', 'vote=165',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 400)
        r = self.client.put('/api/unreads/1', 'vote=a',
            content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 400)
    #TODO: PUT cases

    def test_delete_all(self):
        """Get info of all the comics, get a 200."""
        r = self.client.delete('/api/unreads')
        self.assertEqual(r.status_code, 204)

    def test_delete_one(self):
        """Get info of all the comics, get a 200."""
        r = self.client.delete('/api/unreads/1')
        self.assertEqual(r.status_code, 204)

    def test_deletet_one_invalid(self):
        """Get info of all the comics, get a 200."""
        r = self.client.delete('/api/unreads/100')
        self.assertEqual(r.status_code, 404)
    #TODO: DELETE cases

class StripTests(LoggedInTestCase):
    """Tests for strip related operations."""

    def test_get(self):
        """Get info of a strip, get a 200."""
        r = self.client.get('/api/strips/1')
        self.assertEqual(r.status_code, 200)
        #TODO: what to check?

    def test_get_invalid_id(self):
        """Get infor of a non-existant strips, get a 404."""
        r = self.client.get('/api/strips/10000')
        self.assertEqual(r.status_code, 404)
    #TODO: GET cases

    def test_post(self):
        """POST are not allowed, get a 405."""
        r = self.client.post('/api/strips/123')
        self.assertEqual(r.status_code, 405)

    def test_put_subscribed(self):
        """Mark unread a strip of a subscribed comic, get a 204."""
        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        operations.subscribe_comics([7])

        r = self.client.put('/api/strips/1')
        self.assertEqual(r.status_code, 204)

    def test_put_unsubscribed(self):
        """Mark unread a strip of a unsubscribed comic, get a 400."""
        r = self.client.put('/api/strips/1')
        self.assertEqual(r.status_code, 400)
    #TODO: PUT cases

    def test_delete(self):
        """Mark read a strip of a subscribed comic, get a 204."""
        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        operations.subscribe_comics([7])

        r = self.client.delete('/api/strips/1')
        self.assertEqual(r.status_code, 204)

    def test_delete_unsubscribed(self):
        """Mark read a strip of a unsubscribed comic, get a 400."""
        r = self.client.delete('/api/strips/1')
        self.assertEqual(r.status_code, 400)
    #TODO: DELETE cases

class UserTests(TestCase):
    """Tests for user related operations."""

    fixtures = ['comics.json', 'users.json', 'comichistory.json']

    def setUp(self):
        login_ok = self.client.login(username=test_user, password=test_pwd)
        self.assertTrue(login_ok)

    def test_get(self):
        """Get info of all the comics, get a 200."""
        r = self.client.get('/api/user')
        self.assertEqual(r.status_code, 200)

    def test_post(self):
        """Get info of all the comics, get a 200."""
        r = self.client.post('/api/user')
        self.assertEqual(r.status_code, 405)

    def test_put(self):
        """Get info of all the comics, get a 200."""
        r = self.client.put('/api/user')
        self.assertEqual(r.status_code, 405)

    def test_delete(self):
        """Get info of all the comics, get a 200."""
        r = self.client.delete('/api/user')
        self.assertEqual(r.status_code, 405)

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
    """Tests for comic related operations."""

    fixtures = ['comics.json', 'users.json', 'comichistory.json']

    def setUp(self):
        login_ok = self.client.login(username=test_user, password=test_pwd)
        self.assertTrue(login_ok)

    def test_get_all(self):
        """Get info of all the comics, get a 200."""
        r = self.client.get('/api/comics')
        self.assertEqual(r.status_code, 200)

    def test_get_all_simple(self):
        """Get info of all the comics, get a 200."""
        r = self.client.get('/api/comics/simple')
        self.assertEqual(r.status_code, 200)

    def test_get_one(self):
        """Get info of a comic, get a 200."""
        r = self.client.get('/api/comics/1')
        self.assertEqual(r.status_code, 200)

    def test_get_one_invalid(self):
        """Get info of a comic, get a 404."""
        r = self.client.get('/api/comics/1000')
        self.assertEqual(r.status_code, 404)
    #TODO: GET cases

class StripTests(TestCase):
    """Tests for strip related operations."""

    fixtures = ['comics.json', 'users.json', 'comichistory.json']

    def setUp(self):
        login_ok = self.client.login(username=test_user, password=test_pwd)
        self.assertTrue(login_ok)

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

        r = self.client.put('/api/strips/1?boom=bang')
        self.assertEqual(r.status_code, 204)

    def test_put_unsubscribed(self):
        """Mark unread a strip of a unsubscribed comic, get a 400."""
        r = self.client.put('/api/strips/1')
        self.assertEqual(r.status_code, 400)
    #TODO: PUT cases

    def test_delete(self):
        """Mark unread a strip of a unsubscribed comic, get a 400."""
        r = self.client.delete('/api/strips/1')
        self.assertEqual(r.status_code, 204)
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
        self.assertJSONEqual(smart_text(response.content), '{"meta":{"status":200,"text":"OK"},"response":{"subscriptions":[]}}')

    def test_get_with_subscriptions(self):
        """This get should return a subscriptions set with 2 results."""
        user = User.objects.get(pk=1)
        operations = UserOperations(user)
        operations.subscribe_comics([1, 2, 9])

        response = self.client.get('/api/subscriptions')
        self.assertEqual(response.status_code, 200)

        content = json.loads(smart_text(response.content))
        self.assertEqual('subscriptions' in content['response'].keys(), True)
        self.assertEqual(len(content['response']['subscriptions']), 2)

    #TODO: GET cases
    def test_post_empty_body(self):
        """Force a 400 by not sending an body."""
        response = self.client.post('/api/subscriptions', '', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

    def test_post_empty(self):
        """Send an empty list and get a 400."""
        response = self.client.post('/api/subscriptions', 'subscribe=', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

    def test_post_one(self):
        """Subscribe the user to several comics and get a 204."""
        response = self.client.post('/api/subscriptions', 'subscribe=1,3,2,4', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 204)

    def test_post_several(self):
        """Subscribe the user to several comics and get a 204."""
        response = self.client.post('/api/subscriptions', 'subscribe=1,3,2,4', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 204)

    def test_post_format(self):
        """Subscribe the user to several comics and get a 204."""
        response = self.client.post('/api/subscriptions', 'subscribe=1,3,,2,4', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 204)

    def test_post_format2(self):
        """Subscribe the user to several comics and get a 204."""
        response = self.client.post('/api/subscriptions', 'subscribe=,1,,3,2,4', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 204)

    def test_post_duplicate(self):
        """Subscribe the user to several comics and get a 204."""
        response = self.client.post('/api/subscriptions', 'subscribe=1,2,3,2,4', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 204)

    #TODO: POST cases
    def test_put_empty_body(self):
        """Force a 400 by not sending an body."""
        response = self.client.put('/api/subscriptions', '', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)

    def test_put_none(self):
        """Remove all user subscriptions and get a 204."""
        response = self.client.put('/api/subscriptions','subscriptions=', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 204)

    def test_put_one(self):
        """We will subscribe the user to several comics and we should get a 204."""
        response = self.client.put('/api/subscriptions', 'subscriptions=1', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 204)

    def test_put_several(self):
        """We will subscribe the user to several comics and we should get a 204."""
        response = self.client.put('/api/subscriptions', 'subscriptions=1,3,2,4&boom=bang', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 204)
    #TODO: PUT cases

    def test_delete(self):
        """We will subscribe the user to several comics and we should get a 204."""
        response = self.client.delete('/api/subscriptions')
        self.assertEqual(response.status_code, 200)
    #TODO: DELETE cases

class UnreadTests(TestCase):
    """Tests for unread comics related operations."""

    fixtures = ['comics.json', 'users.json', 'comichistory.json']

    def setUp(self):
        login_ok = self.client.login(username=test_user, password=test_pwd)
        self.assertTrue(login_ok)

    def test_get_all(self):
        """Get info of all the comics, get a 200."""
        r = self.client.get('/api/unreads')
        self.assertEqual(r.status_code, 200)

    def test_get_all_simple(self):
        """Get info of all the unreads, get a 200."""
        r = self.client.get('/api/unreads/simple')
        self.assertEqual(r.status_code, 200)

    def test_get_one(self):
        """Get info of all the comics, get a 200."""
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

    def test_post_all_simple(self):
        """Get info of all the unreads, get a 200."""
        r = self.client.post('/api/unreads/simple')
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

    def test_put_all_simple(self):
        """Get info of all the unreads, get a 200."""
        r = self.client.put('/api/unreads/simple')
        self.assertEqual(r.status_code, 405)

    def test_put_ok(self):
        """Get info of all the comics, get a 200."""
        r = self.client.put('/api/unreads/1', 'vote=1', content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 204)

    def test_put_invalid_comic(self):
        """Get info of all the comics, get a 200."""
        r = self.client.put('/api/unreads/100', 'vote=1', content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 404)

    def test_put_invalid_vote(self):
        """Get info of all the comics, get a 200."""
        r = self.client.put('/api/unreads/1')
        self.assertEqual(r.status_code, 400)
        r = self.client.put('/api/unreads/1', 'vote=165', content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 400)
        r = self.client.put('/api/unreads/1', 'vote=a', content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 400)
    #TODO: PUT cases

    def test_delete_all(self):
        """Get info of all the comics, get a 200."""
        r = self.client.delete('/api/unreads')
        self.assertEqual(r.status_code, 204)

    def test_delete_all_simple(self):
        """Get info of all the unreads, get a 200."""
        r = self.client.delete('/api/unreads/simple')
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

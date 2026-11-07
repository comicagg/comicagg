from types import SimpleNamespace

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, get_hashers, identify_hasher
from django.contrib.auth.models import User
from django.contrib.messages import WARNING, get_messages
from django.contrib.messages.storage.base import Message
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.client import RequestFactory

from middleware import MAINTENANCE_MESSAGE, MaintenanceMiddleware

from .hashers import LegacySHA1PasswordHasher
from .settings import PASSWORD_HASHERS

LEGACY_PASSWORD = "sha1$salt$59b3e8d637cf97edbe2384cf59cb7453dfe30789"


class LegacySHA1PasswordHasherTests(SimpleTestCase):
    def test_legacy_hash(self):
        hasher = LegacySHA1PasswordHasher()
        self.assertEqual(hasher.encode("password", "salt"), LEGACY_PASSWORD)
        self.assertTrue(hasher.verify("password", LEGACY_PASSWORD))
        self.assertFalse(hasher.verify("incorrect", LEGACY_PASSWORD))

    def test_unicode_password(self):
        hasher = LegacySHA1PasswordHasher()
        encoded = "sha1$salty$9ce67ffcd955a5070b3adb2134bbe3986e0b595f"
        self.assertEqual(hasher.encode("p\u00e4ssw\u00f6rd", "salty"), encoded)
        self.assertTrue(hasher.verify("p\u00e4ssw\u00f6rd", encoded))

    def test_safe_summary(self):
        summary = LegacySHA1PasswordHasher().safe_summary(LEGACY_PASSWORD)
        self.assertEqual(summary["algorithm"], "sha1")
        self.assertEqual(summary["salt"], "sa**")
        self.assertEqual(summary["hash"], "59b3e8" + "*" * 34)


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS)
class PasswordAuthenticationTests(TestCase):
    def test_configured_hashers_load(self):
        hashers = get_hashers()
        self.assertEqual(len(hashers), len(PASSWORD_HASHERS))
        self.assertEqual(hashers[0].algorithm, "pbkdf2_sha256")
        self.assertIsInstance(hashers[-1], LegacySHA1PasswordHasher)

    def test_legacy_login_upgrades_stored_password(self):
        user = User.objects.create(username="legacy", password=LEGACY_PASSWORD)

        authenticated_user = authenticate(username="legacy", password="password")

        self.assertEqual(authenticated_user, user)
        user.refresh_from_db()
        self.assertEqual(identify_hasher(user.password).algorithm, "pbkdf2_sha256")
        self.assertTrue(check_password("password", user.password))

    def test_incorrect_legacy_password_is_not_upgraded(self):
        user = User.objects.create(username="legacy", password=LEGACY_PASSWORD)

        self.assertIsNone(authenticate(username="legacy", password="incorrect"))

        user.refresh_from_db()
        self.assertEqual(user.password, LEGACY_PASSWORD)

    def test_modern_login(self):
        user = User.objects.create_user(username="modern", password="password")
        original_password = user.password
        self.assertEqual(identify_hasher(original_password).algorithm, "pbkdf2_sha256")

        self.assertEqual(authenticate(username="modern", password="password"), user)
        self.assertIsNone(authenticate(username="modern", password="incorrect"))

        user.refresh_from_db()
        self.assertEqual(user.password, original_password)


@override_settings(MAINTENANCE=1)
class MaintenanceMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        self.request.user = SimpleNamespace(is_authenticated=True, is_superuser=True)
        self.request.session = {}
        self.request._messages = FallbackStorage(self.request)
        self.middleware = MaintenanceMiddleware(lambda request: HttpResponse())

    def test_notice_is_not_added_when_already_queued(self):
        self.request._messages.add(WARNING, MAINTENANCE_MESSAGE)

        self.middleware(self.request)

        self.assertEqual(len(list(get_messages(self.request))), 1)

    def test_notice_is_not_added_when_already_loaded(self):
        self.request._messages._loaded_data = [Message(WARNING, MAINTENANCE_MESSAGE)]

        self.middleware(self.request)

        self.assertEqual(len(list(get_messages(self.request))), 1)

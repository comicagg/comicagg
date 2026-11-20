import json
import re
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

from django.db import connection, connections
from django.http import HttpResponse
from django.test import (
    RequestFactory,
    TestCase,
    TransactionTestCase,
    skipUnlessDBFeature,
)
from django.test.utils import CaptureQueriesContext

from accounts.models import User

from ..ajax.views import mark_all_read, mark_read
from ..fields import ComicStatus
from ..models import Comic, Strip, Subscription, UnreadStrip
from ..read_state import InvalidReadSnapshot, make_snapshot
from ..tasks.distribute_strips import distribute_comic_strips
from ..tasks.max_unreads import max_unreads_per_user
from ..views import read_view


class ReadMarkerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="reader")
        self.comic = Comic.objects.create(name="Comic", status=ComicStatus.ACTIVE)
        self.other = Comic.objects.create(name="Other", status=ComicStatus.ACTIVE)
        self.subscription = Subscription.objects.create(
            user=self.user, comic=self.comic
        )
        Subscription.objects.create(user=self.user, comic=self.other)
        self.factory = RequestFactory()

    def unread(self, comic=None):
        comic = comic or self.comic
        strip = Strip.objects.create(
            comic=comic, url="https://example.com/strip", unreads_distributed=True
        )
        return UnreadStrip.objects.create(user=self.user, comic=comic, strip=strip)

    def snapshot(self):
        return make_snapshot(
            self.user.pk,
            list(self.user.subscriptions),
            list(self.user.unread_strips.all()),
        )

    def test_comic_clear_preserves_later_arrivals_and_defers_deletion(self):
        old = self.unread()
        token = self.snapshot()
        later = self.unread()
        self.user.mark_read(self.comic, snapshot=token)
        self.assertEqual(list(self.user.unread_strips), [later])
        self.assertTrue(UnreadStrip.objects.filter(pk=old.pk).exists())
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.read_through, old.read_sequence)

    def test_arrival_order_does_not_depend_on_primary_key_order(self):
        first_strip = Strip.objects.create(
            comic=self.comic, url="https://example.com/first", unreads_distributed=True
        )
        UnreadStrip.objects.create(
            pk=1000000000, user=self.user, comic=self.comic, strip=first_strip
        )
        token = self.snapshot()
        later_strip = Strip.objects.create(
            comic=self.comic, url="https://example.com/later", unreads_distributed=True
        )
        later = UnreadStrip.objects.create(
            pk=999999999, user=self.user, comic=self.comic, strip=later_strip
        )
        self.user.mark_read_all(snapshot=token)
        self.assertEqual(list(self.user.unread_strips), [later])

    def test_all_clear_uses_each_comics_displayed_boundary(self):
        self.unread()
        self.unread(self.other)
        token = self.snapshot()
        later = [self.unread(), self.unread(self.other)]
        self.user.mark_read_all(snapshot=token)
        self.assertCountEqual(self.user.unread_strips, later)
        self.assertEqual(UnreadStrip.objects.count(), 4)

    def test_vote_preserves_new_strips_and_updates_votes(self):
        self.unread()
        token = self.snapshot()
        later = self.unread()
        self.user.mark_read(self.comic, 1, snapshot=token)
        self.comic.refresh_from_db()
        self.assertEqual(self.comic.total_votes, 1)
        self.assertEqual(self.comic.positive_votes, 1)
        self.assertEqual(list(self.user.unread_strips), [later])

    def test_stale_tab_cannot_move_marker_backwards(self):
        self.unread()
        first = self.snapshot()
        self.unread()
        self.user.mark_read_all(snapshot=self.snapshot())
        self.user.mark_read_all(snapshot=first)
        self.assertFalse(self.user.unread_strips.exists())

    def test_old_snapshot_cannot_affect_replacement_subscription_or_votes(self):
        self.unread()
        token = self.snapshot()
        self.user.unsubscribe(self.comic)
        self.user.subscribe(self.comic)
        later = self.unread()
        self.user.mark_read(self.comic, 1, snapshot=token)
        self.assertEqual(list(self.user.unread_strips), [later])
        self.comic.refresh_from_db()
        self.assertEqual(self.comic.total_votes, 0)

    def test_subscription_does_not_create_unread(self):
        self.user.unsubscribe(self.comic)
        Strip.objects.create(comic=self.comic, url="https://example.com/latest")
        self.user.subscribe(self.comic)
        self.assertFalse(UnreadStrip.objects.exists())

    def test_mark_unread_replaces_read_latest_without_resurrecting_older(self):
        older = self.unread()
        latest = self.unread()
        self.user.mark_read_all(snapshot=self.snapshot())
        self.assertTrue(self.user.mark_unread(self.comic))
        current = self.user.unread_strips.get()
        self.assertEqual(current.strip_id, latest.strip_id)
        self.assertGreater(current.read_sequence, latest.read_sequence)
        self.assertNotEqual(current.strip_id, older.strip_id)
        self.assertFalse(self.user.mark_unread(self.comic))

    def test_mark_unread_does_not_change_existing_unreads(self):
        current = self.unread()
        self.assertFalse(self.user.mark_unread(self.comic))
        self.assertEqual(list(self.user.unread_strips), [current])

    def test_mark_unread_adds_latest_without_removing_existing_older_unread(self):
        older = self.unread()
        latest = Strip.objects.create(
            comic=self.comic,
            url="https://example.com/latest",
            unreads_distributed=True,
        )
        self.assertTrue(self.user.mark_unread(self.comic))
        self.assertCountEqual(
            self.user.unread_strips.values_list("strip_id", flat=True),
            [older.strip_id, latest.pk],
        )

    def test_unsubscribe_forgets_all_rows_and_prevents_redelivery(self):
        self.unread()
        self.user.mark_read_all(snapshot=self.snapshot())
        self.unread()
        Strip.objects.create(comic=self.comic, url="https://example.com/pending")
        self.user.unsubscribe(self.comic)
        distribute_comic_strips(self.comic.pk)
        self.assertFalse(UnreadStrip.objects.exists())
        self.assertFalse(self.user.subscription_set.filter(comic=self.comic).exists())

    def test_empty_snapshot_does_not_clear_new_arrivals(self):
        token = self.snapshot()
        later = self.unread()
        self.user.mark_read_all(snapshot=token)
        self.assertEqual(list(self.user.unread_strips), [later])

    def test_hidden_comics_are_not_cleared_by_reader_snapshot(self):
        self.comic.status = ComicStatus.INACTIVE
        self.comic.save()
        old = self.unread()
        self.user.mark_read_all(snapshot=self.snapshot())
        self.assertTrue(UnreadStrip.objects.active().filter(pk=old.pk).exists())

    def test_cached_counts_and_lists_are_invalidated(self):
        self.unread()
        self.assertEqual(self.user.comics_unread_count, 1)
        list(self.user.unread_strips)
        self.user.mark_read_all(snapshot=self.snapshot())
        self.assertEqual(self.user.comics_unread_count, 0)
        self.assertEqual(list(self.user.unread_strips), [])

    def test_snapshot_is_user_bound_and_tamper_proof(self):
        self.unread()
        token = self.snapshot()
        other_user = User.objects.create(username="not-reader")
        with self.assertRaises(InvalidReadSnapshot):
            other_user.mark_read_all(snapshot=token)
        with self.assertRaises(InvalidReadSnapshot):
            self.user.mark_read_all(snapshot=token + "tampered")

    def test_ajax_requires_post_and_valid_snapshot(self):
        for view in (mark_read, mark_all_read):
            request = self.factory.get("/")
            request.user = self.user
            self.assertEqual(view(request).status_code, 405)
            request = self.factory.post("/", {"id": self.comic.pk, "value": "0"})
            request.user = self.user
            self.assertEqual(view(request).status_code, 400)
            for token in ("", "invalid"):
                request = self.factory.post(
                    "/", {"id": self.comic.pk, "value": "0", "snapshot": token}
                )
                request.user = self.user
                self.assertEqual(view(request).status_code, 400)

    def test_ajax_snapshot_clears_only_displayed_rows(self):
        self.unread()
        token = self.snapshot()
        later = self.unread()
        request = self.factory.post(
            "/", {"id": self.comic.pk, "value": "0", "snapshot": token}
        )
        request.user = self.user
        response = mark_read(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(self.user.unread_strips), [later])

    def test_reader_signs_the_rendered_rows_not_later_arrivals(self):
        displayed = self.unread()
        request = self.factory.get("/comics/read/")
        request.user = self.user
        request.consent = SimpleNamespace(accepted=True)
        tokens = []
        later = []

        def capture_snapshot(*args):
            later.append(self.unread())
            token = make_snapshot(*args)
            tokens.append(token)
            return token

        with (
            patch("comics.views._find_random_comic", return_value=None),
            patch("comics.views.make_snapshot", side_effect=capture_snapshot),
            patch("comics.views.render", return_value=HttpResponse()) as render,
        ):
            read_view(request)
        context = render.call_args.args[2]
        displayed_rows = dict((comic.pk, rows) for comic, rows in context["comic_list"])
        self.assertEqual(displayed_rows[self.comic.pk], [displayed])
        self.assertEqual(context["read_snapshot"], tokens[0])
        self.user.mark_read_all(snapshot=tokens[0])
        self.assertEqual(list(self.user.unread_strips), later)

    def test_reader_template_embeds_a_valid_snapshot(self):
        self.unread()
        request = self.factory.get("/comics/read/")
        request.user = self.user
        request.consent = SimpleNamespace(accepted=True)
        with patch("comics.views._find_random_comic", return_value=None):
            response = read_view(request)
        match = re.search(
            r'<script id="read-snapshot" type="application/json">(.*?)</script>',
            response.content.decode(),
        )
        self.assertIsNotNone(match)
        token = json.loads(unescape(match.group(1)))
        self.user.mark_read_all(snapshot=token)
        self.assertFalse(self.user.unread_strips.exists())

    def test_read_actions_do_not_delete_or_update_unread_rows(self):
        for _ in range(25):
            self.unread()
        token = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            self.user.mark_read_all(snapshot=token)
        mutations = [
            query["sql"]
            for query in queries
            if query["sql"].lstrip().startswith(("UPDATE", "DELETE", "INSERT"))
        ]
        self.assertEqual(len(mutations), 1)
        self.assertIn("comics_subscription", mutations[0])
        self.assertEqual(UnreadStrip.objects.count(), 25)

    def test_subscription_queryset_delete_removes_unreads_and_marker(self):
        self.unread()
        self.user.mark_read_all(snapshot=self.snapshot())
        self.user.subscription_set.filter(comic=self.comic).delete()
        self.assertFalse(UnreadStrip.objects.exists())
        self.assertFalse(self.user.subscription_set.filter(comic=self.comic).exists())

    def test_deleting_stale_subscription_instance_preserves_replacement_state(self):
        stale = Subscription.objects.get(pk=self.subscription.pk)
        self.user.unsubscribe(self.comic)
        self.user.subscribe(self.comic)
        current = self.unread()
        stale.delete()
        self.assertEqual(list(self.user.unread_strips), [current])

    def test_stale_model_saves_do_not_reset_counters_or_markers(self):
        stale_comic = Comic.objects.get(pk=self.comic.pk)
        stale_subscription = Subscription.objects.get(pk=self.subscription.pk)
        unread = self.unread()
        self.user.mark_read_all(snapshot=self.snapshot())
        stale_comic.name = "Renamed"
        stale_comic.save()
        stale_subscription.position = 2
        stale_subscription.save()
        self.comic.refresh_from_db()
        self.subscription.refresh_from_db()
        self.assertEqual(self.comic.unread_sequence, unread.read_sequence)
        self.assertEqual(self.subscription.read_through, unread.read_sequence)

    def test_cleanup_deletes_only_logically_read_rows_in_bounded_batches(self):
        from ..tasks.cleanup_read_strips import cleanup_read_strips

        old = [self.unread(), self.unread()]
        self.user.mark_read_all(snapshot=self.snapshot())
        later = self.unread()
        self.assertEqual(cleanup_read_strips(batch_size=1, max_batches=1), 1)
        self.assertEqual(
            UnreadStrip.objects.filter(pk__in=[r.pk for r in old]).count(), 1
        )
        self.assertEqual(cleanup_read_strips(batch_size=1, max_batches=5), 1)
        self.assertEqual(list(UnreadStrip.objects.all()), [later])

    def test_cleanup_keeps_pending_delivery_deduplication_until_distribution(self):
        from ..tasks.cleanup_read_strips import cleanup_read_strips

        strip = Strip.objects.create(
            comic=self.comic, url="https://example.com/pending"
        )
        self.user.mark_unread(self.comic)
        self.user.mark_read_all(snapshot=self.snapshot())
        self.assertEqual(cleanup_read_strips(), 0)
        distribute_comic_strips(self.comic.pk)
        self.assertFalse(self.user.unread_strips.exists())
        self.assertEqual(cleanup_read_strips(), 1)
        distribute_comic_strips(self.comic.pk)
        self.assertFalse(self.user.unread_strips.exists())
        strip.refresh_from_db()
        self.assertTrue(strip.unreads_distributed)

    def test_unread_limit_ignores_read_rows_and_handles_every_user(self):
        users = [self.user, User.objects.create(username="second-reader")]
        Subscription.objects.create(user=users[1], comic=self.comic)
        for user in users:
            old = Strip.objects.create(
                comic=self.comic,
                url="https://example.com/old",
                unreads_distributed=True,
            )
            UnreadStrip.objects.create(user=user, comic=self.comic, strip=old)
            user.mark_read_all(
                snapshot=make_snapshot(
                    user.pk, list(user.subscriptions), list(user.unread_strips)
                )
            )
            for _ in range(3):
                strip = Strip.objects.create(
                    comic=self.comic,
                    url="https://example.com/new",
                    unreads_distributed=True,
                )
                UnreadStrip.objects.create(user=user, comic=self.comic, strip=strip)
        with self.settings(MAX_UNREADS_PER_USER=2):
            max_unreads_per_user()
        for user in users:
            self.assertEqual(user.unread_strips.count(), 2)
            self.assertEqual(user.unreadstrip_set.count(), 3)


class ReadMarkerConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create(username="concurrent-reader")
        self.comic = Comic.objects.create(name="Concurrent", status=ComicStatus.ACTIVE)
        Subscription.objects.create(user=self.user, comic=self.comic)

    def snapshot(self):
        user = User.objects.get(pk=self.user.pk)
        return make_snapshot(
            user.pk, list(user.subscriptions), list(user.unread_strips)
        )

    @skipUnlessDBFeature("has_select_for_update")
    def test_inflight_distribution_survives_old_page_clear(self):
        old_strip = Strip.objects.create(
            comic=self.comic, url="https://example.com/old", unreads_distributed=True
        )
        UnreadStrip.objects.create(user=self.user, comic=self.comic, strip=old_strip)
        token = self.snapshot()
        pending = Strip.objects.create(comic=self.comic, url="https://example.com/new")
        inserted = Event()
        release = Event()
        original = UnreadStrip.objects.bulk_create

        def block_commit(*args, **kwargs):
            result = original(*args, **kwargs)
            inserted.set()
            if not release.wait(10):
                raise TimeoutError("Distribution was not released")
            return result

        def distribute():
            try:
                distribute_comic_strips(self.comic.pk)
            finally:
                connections.close_all()

        with (
            patch.object(UnreadStrip.objects, "bulk_create", side_effect=block_commit),
            ThreadPoolExecutor(max_workers=1) as workers,
        ):
            future = workers.submit(distribute)
            try:
                self.assertTrue(inserted.wait(10))
                self.user.mark_read_all(snapshot=token)
            finally:
                release.set()
            future.result(10)
        self.assertEqual(
            list(self.user.unread_strips.values_list("strip_id", flat=True)),
            [pending.pk],
        )

    @skipUnlessDBFeature("has_select_for_update")
    def test_unsubscribe_waits_for_distribution_and_removes_its_rows(self):
        Strip.objects.create(comic=self.comic, url="https://example.com/pending")
        inserted = Event()
        removing = Event()
        release = Event()
        original = UnreadStrip.objects.bulk_create

        def block_commit(*args, **kwargs):
            result = original(*args, **kwargs)
            inserted.set()
            if not release.wait(10):
                raise TimeoutError("Distribution was not released")
            return result

        def distribute():
            try:
                distribute_comic_strips(self.comic.pk)
            finally:
                connections.close_all()

        def unsubscribe():
            try:
                removing.set()
                User.objects.get(pk=self.user.pk).unsubscribe(self.comic)
            finally:
                connections.close_all()

        with (
            patch.object(UnreadStrip.objects, "bulk_create", side_effect=block_commit),
            ThreadPoolExecutor(max_workers=2) as workers,
        ):
            distribution = workers.submit(distribute)
            try:
                self.assertTrue(inserted.wait(10))
                removal = workers.submit(unsubscribe)
                self.assertTrue(removing.wait(10))
            finally:
                release.set()
            distribution.result(10)
            removal.result(10)
        self.assertFalse(UnreadStrip.objects.filter(user=self.user).exists())
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())

    @skipUnlessDBFeature("has_select_for_update")
    def test_manual_unread_waits_for_distribution_and_remains_visible(self):
        pending = Strip.objects.create(
            comic=self.comic, url="https://example.com/pending"
        )
        latest = Strip.objects.create(
            comic=self.comic,
            url="https://example.com/latest",
            unreads_distributed=True,
        )
        inserted = Event()
        marking = Event()
        release = Event()
        original = UnreadStrip.objects.bulk_create

        def block_commit(*args, **kwargs):
            result = original(*args, **kwargs)
            inserted.set()
            if not release.wait(10):
                raise TimeoutError("Distribution was not released")
            return result

        def distribute():
            try:
                distribute_comic_strips(self.comic.pk)
            finally:
                connections.close_all()

        def mark_unread():
            try:
                marking.set()
                return User.objects.get(pk=self.user.pk).mark_unread(self.comic)
            finally:
                connections.close_all()

        with (
            patch.object(UnreadStrip.objects, "bulk_create", side_effect=block_commit),
            ThreadPoolExecutor(max_workers=2) as workers,
        ):
            distribution = workers.submit(distribute)
            try:
                self.assertTrue(inserted.wait(10))
                manual = workers.submit(mark_unread)
                self.assertTrue(marking.wait(10))
            finally:
                release.set()
            distribution.result(10)
            self.assertTrue(manual.result(10))
        rows = {row.strip_id: row.read_sequence for row in self.user.unread_strips}
        self.assertEqual(set(rows), {pending.pk, latest.pk})
        self.assertGreater(rows[latest.pk], rows[pending.pk])

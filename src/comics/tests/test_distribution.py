from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from threading import Event
from unittest.mock import call, patch

from django.core.management import call_command
from django.db import IntegrityError, connections, transaction
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django_celery_beat.models import MINUTES, PeriodicTask

from accounts.models import User

from ..fields import ComicStatus
from ..models import Comic, Strip, Subscription, UnreadStrip
from ..read_state import make_snapshot
from ..update import update_comic


class DistributionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.comic = Comic.objects.create(name="Distribution", status=ComicStatus.ACTIVE)
        cls.other_comic = Comic.objects.create(name="Other", status=ComicStatus.ACTIVE)
        cls.user = User.objects.create(username="reader")
        cls.other_user = User.objects.create(username="other-reader")
        cls.inactive_user = User.objects.create(
            username="inactive-reader", is_active=False
        )
        cls.non_subscriber = User.objects.create(username="non-subscriber")
        for user in (cls.user, cls.other_user, cls.inactive_user):
            Subscription.objects.create(user=user, comic=cls.comic)
        Subscription.objects.create(user=cls.non_subscriber, comic=cls.other_comic)

    def create_strip(self, comic=None, **kwargs):
        return Strip.objects.create(
            comic=comic or self.comic, url="https://example.com/strip.png", **kwargs
        )

    def distribute(self):
        from ..tasks.distribute_strips import distribute_comic_strips

        return distribute_comic_strips(self.comic.pk)

    def test_strip_creation_defers_distribution(self):
        strip = self.create_strip()

        self.assertFalse(strip.unreads_distributed)
        self.assertFalse(UnreadStrip.objects.exists())

    def test_dispatcher_enqueues_one_task_per_pending_comic(self):
        from ..tasks.distribute_strips import distribute_pending_strips

        self.create_strip()
        self.create_strip()
        self.create_strip(comic=self.other_comic)
        completed_comic = Comic.objects.create(name="Completed")
        self.create_strip(comic=completed_comic, unreads_distributed=True)

        with patch(
            "comics.tasks.distribute_strips.distribute_comic_strips.delay"
        ) as enqueue:
            distribute_pending_strips()

        self.assertCountEqual(
            enqueue.call_args_list,
            [call(self.comic.pk), call(self.other_comic.pk)],
        )
        self.assertFalse(UnreadStrip.objects.exists())

    def test_empty_dispatcher_does_not_enqueue_tasks(self):
        from ..tasks.distribute_strips import distribute_pending_strips

        with patch(
            "comics.tasks.distribute_strips.distribute_comic_strips.delay"
        ) as enqueue:
            distribute_pending_strips()

        enqueue.assert_not_called()

    def test_distributes_all_pending_strips_to_active_subscribers_only(self):
        strips = [self.create_strip(), self.create_strip()]
        completed = self.create_strip(unreads_distributed=True)
        other = self.create_strip(comic=self.other_comic)

        self.distribute()

        self.assertCountEqual(
            UnreadStrip.objects.values_list("user_id", "strip_id", "comic_id"),
            [
                (user.pk, strip.pk, self.comic.pk)
                for user in (self.user, self.other_user)
                for strip in strips
            ],
        )
        for strip in strips + [completed]:
            strip.refresh_from_db()
            self.assertTrue(strip.unreads_distributed)
        other.refresh_from_db()
        self.assertFalse(other.unreads_distributed)

    def test_bulk_created_strips_are_pending_and_distributed(self):
        Strip.objects.bulk_create(
            [
                Strip(comic=self.comic, url=f"https://example.com/{i}.png")
                for i in range(2)
            ]
        )

        self.distribute()

        self.assertEqual(UnreadStrip.objects.count(), 4)
        self.assertFalse(Strip.objects.filter(unreads_distributed=False).exists())

    def test_repeated_distribution_does_not_restore_read_strips(self):
        strip = self.create_strip()
        self.distribute()
        self.user.mark_read(
            self.comic,
            snapshot=make_snapshot(
                self.user.pk,
                list(self.user.subscriptions),
                list(self.user.unread_strips),
            ),
        )

        self.distribute()

        self.assertFalse(UnreadStrip.objects.active().filter(user=self.user).exists())
        self.assertEqual(
            UnreadStrip.objects.filter(user=self.other_user, strip=strip).count(), 1
        )

    def test_existing_unread_row_is_preserved(self):
        strip = self.create_strip()
        existing = UnreadStrip.objects.create(
            user=self.user, comic=self.comic, strip=strip
        )

        self.distribute()

        self.assertTrue(UnreadStrip.objects.filter(pk=existing.pk).exists())
        self.assertEqual(UnreadStrip.objects.count(), 2)

    def test_subscribe_creates_no_unread_until_distribution(self):
        self.create_strip()
        self.non_subscriber.subscribe(self.comic)
        self.assertFalse(UnreadStrip.objects.filter(user=self.non_subscriber).exists())
        self.distribute()

        self.assertEqual(
            UnreadStrip.objects.filter(
                user=self.non_subscriber, comic=self.comic
            ).count(),
            1,
        )

    def test_mark_unread_handles_a_concurrently_created_unread(self):
        strip = self.create_strip(unreads_distributed=True)
        UnreadStrip.objects.create(user=self.user, comic=self.comic, strip=strip)

        with patch("django.db.models.query.QuerySet.count", return_value=0):
            self.assertFalse(self.user.mark_unread(self.comic))

        self.assertEqual(UnreadStrip.objects.filter(user=self.user).count(), 1)

    def test_no_subscribers_still_completes_distribution(self):
        strip = self.create_strip(comic=self.other_comic)
        Subscription.objects.filter(comic=self.other_comic).delete()
        from ..tasks.distribute_strips import distribute_comic_strips

        distribute_comic_strips(self.other_comic.pk)

        strip.refresh_from_db()
        self.assertTrue(strip.unreads_distributed)
        self.assertFalse(UnreadStrip.objects.exists())

    def test_subscriptions_are_evaluated_at_execution(self):
        strip = self.create_strip()
        self.user.unsubscribe(self.comic)
        Subscription.objects.create(user=self.non_subscriber, comic=self.comic)

        self.distribute()

        self.assertCountEqual(
            UnreadStrip.objects.filter(strip=strip).values_list("user_id", flat=True),
            [self.other_user.pk, self.non_subscriber.pk],
        )

    def test_bulk_inserts_are_bounded_and_batch_across_strips(self):
        for _ in range(3):
            self.create_strip()

        with (
            patch("comics.tasks.distribute_strips.BATCH_SIZE", 3),
            patch.object(
                UnreadStrip.objects,
                "bulk_create",
                wraps=UnreadStrip.objects.bulk_create,
            ) as insert,
        ):
            self.distribute()

        self.assertEqual(insert.call_count, 2)
        for invocation in insert.call_args_list:
            self.assertEqual(len(invocation.args[0]), 3)
            self.assertEqual(invocation.kwargs["batch_size"], 3)
        self.assertEqual(UnreadStrip.objects.count(), 6)

    def test_failed_batch_rolls_back_and_can_be_retried(self):
        for _ in range(2):
            self.create_strip()
        original_insert = UnreadStrip.objects.bulk_create
        insert_count = 0

        def fail_second_batch(*args, **kwargs):
            nonlocal insert_count
            insert_count += 1
            if insert_count == 2:
                raise IntegrityError("Distribution failed")
            return original_insert(*args, **kwargs)

        with (
            patch("comics.tasks.distribute_strips.BATCH_SIZE", 2),
            patch.object(
                UnreadStrip.objects, "bulk_create", side_effect=fail_second_batch
            ),
            self.assertRaisesMessage(IntegrityError, "Distribution failed"),
        ):
            self.distribute()

        self.assertFalse(UnreadStrip.objects.exists())
        self.assertEqual(Strip.objects.filter(unreads_distributed=False).count(), 2)
        self.distribute()
        self.assertEqual(UnreadStrip.objects.count(), 4)

    def test_new_strip_during_distribution_remains_pending(self):
        initial = self.create_strip()
        original_insert = UnreadStrip.objects.bulk_create
        later = []

        def insert_with_new_strip(*args, **kwargs):
            later.append(self.create_strip())
            return original_insert(*args, **kwargs)

        with patch.object(
            UnreadStrip.objects, "bulk_create", side_effect=insert_with_new_strip
        ):
            self.distribute()

        initial.refresh_from_db()
        later[0].refresh_from_db()
        self.assertTrue(initial.unreads_distributed)
        self.assertFalse(later[0].unreads_distributed)
        self.assertFalse(UnreadStrip.objects.filter(strip=later[0]).exists())
        self.distribute()
        self.assertEqual(UnreadStrip.objects.count(), 4)

    def test_user_strip_pair_is_unique(self):
        strip = self.create_strip()
        UnreadStrip.objects.create(user=self.user, comic=self.comic, strip=strip)

        with transaction.atomic(), self.assertRaises(IntegrityError):
            UnreadStrip.objects.create(user=self.user, comic=self.comic, strip=strip)

    def test_default_update_creates_pending_strip_without_unreads(self):
        self.comic.re1_url = "https://example.com/"
        self.comic.re1_base = "%s"
        self.comic.re1_re = r"(https://example.com/new.png)"
        with patch(
            "comics.update._download_url",
            side_effect=lambda url: ["https://example.com/new.png"],
        ):
            self.assertTrue(update_comic(self.comic))
            self.assertFalse(update_comic(self.comic))

        strip = Strip.objects.get(comic=self.comic)
        self.assertFalse(strip.unreads_distributed)
        self.assertFalse(UnreadStrip.objects.exists())
        self.distribute()
        self.assertEqual(UnreadStrip.objects.count(), 2)

    def test_custom_update_defers_all_new_strips(self):
        self.comic.custom_func = (
            'strip_set.extend([Strip(comic=comic, url="https://example.com/new.png"), '
            'Strip(comic=comic, url="https://example.com/older.png")])'
        )

        self.assertTrue(update_comic(self.comic))
        self.assertFalse(update_comic(self.comic))

        self.assertEqual(Strip.objects.filter(unreads_distributed=False).count(), 2)
        self.assertFalse(UnreadStrip.objects.exists())
        self.distribute()
        self.assertEqual(UnreadStrip.objects.count(), 4)

    def test_schedule_is_every_fifteen_minutes_and_registration_is_idempotent(self):
        for _ in range(2):
            call_command("ensure_tasks", stdout=StringIO())

        task = PeriodicTask.objects.get(
            task="comics.tasks.distribute_strips.distribute_pending_strips"
        )
        self.assertTrue(task.enabled)
        self.assertEqual(task.interval.period, MINUTES)
        self.assertEqual(task.interval.every, 15)
        cleanup = PeriodicTask.objects.get(
            task="comics.tasks.cleanup_read_strips.cleanup_read_strips"
        )
        self.assertTrue(cleanup.enabled)
        self.assertEqual(cleanup.interval.period, MINUTES)
        self.assertEqual(cleanup.interval.every, 15)

    def test_schedule_dry_run_does_not_create_tasks(self):
        output = StringIO()
        call_command("ensure_tasks", dry=True, stdout=output)

        self.assertFalse(PeriodicTask.objects.exists())


class DistributionConcurrencyTests(TransactionTestCase):
    @skipUnlessDBFeature("has_select_for_update")
    def test_overlapping_comic_tasks_serialize_and_distribute_only_once(self):
        from ..tasks.distribute_strips import distribute_comic_strips

        comic = Comic.objects.create(name="Concurrent", status=ComicStatus.ACTIVE)
        user = User.objects.create(username="concurrent-reader")
        Subscription.objects.create(user=user, comic=comic)
        strip = Strip.objects.create(comic=comic, url="https://example.com/strip.png")
        first_insert = Event()
        second_started = Event()
        release_first = Event()
        original_insert = UnreadStrip.objects.bulk_create

        def block_first_insert(*args, **kwargs):
            first_insert.set()
            if not release_first.wait(timeout=10):
                raise TimeoutError("Timed out waiting to release the first worker")
            return original_insert(*args, **kwargs)

        def run_distribution(started=None):
            try:
                if started:
                    started.set()
                return distribute_comic_strips(comic.pk)
            finally:
                connections.close_all()

        with (
            patch.object(
                UnreadStrip.objects, "bulk_create", side_effect=block_first_insert
            ) as insert,
            ThreadPoolExecutor(max_workers=2) as workers,
        ):
            first = workers.submit(run_distribution)
            try:
                self.assertTrue(first_insert.wait(timeout=10))
                second = workers.submit(run_distribution, second_started)
                self.assertTrue(second_started.wait(timeout=10))
                self.assertFalse(second.done())
            finally:
                release_first.set()
            self.assertEqual(first.result(timeout=10), {"strips": 1, "unreads": 1})
            self.assertEqual(second.result(timeout=10), {"strips": 0, "unreads": 0})

        self.assertEqual(insert.call_count, 1)
        self.assertEqual(UnreadStrip.objects.filter(user=user, strip=strip).count(), 1)

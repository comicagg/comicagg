from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ReadMarkerMigrationTests(TransactionTestCase):
    def test_existing_unreads_and_subscription_order_are_preserved(self):
        before = [("comics", "0015_deferred_strip_distribution")]
        after = [("comics", "0016_read_markers")]
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(latest))
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        comic = apps.get_model("comics", "Comic").objects.create(name="Historical")
        empty_comic = apps.get_model("comics", "Comic").objects.create(name="Empty")
        user = apps.get_model("auth", "User").objects.create(username="reader")
        subscriptions = apps.get_model("comics", "Subscription").objects
        subscriptions.create(user=user, comic=comic, position=5)
        kept = subscriptions.create(user=user, comic=comic, position=2)
        strip = apps.get_model("comics", "Strip").objects.create(
            comic=comic, url="https://example.com/strip"
        )
        unread = apps.get_model("comics", "UnreadStrip").objects.create(
            user=user, comic=comic, strip=strip
        )
        executor = MigrationExecutor(connection)
        executor.migrate(after)
        apps = executor.loader.project_state(after).apps
        self.assertEqual(
            apps.get_model("comics", "UnreadStrip")
            .objects.get(pk=unread.pk)
            .read_sequence,
            unread.pk,
        )
        self.assertEqual(
            apps.get_model("comics", "Comic").objects.get(pk=comic.pk).unread_sequence,
            unread.pk,
        )
        self.assertEqual(
            apps.get_model("comics", "Comic")
            .objects.get(pk=empty_comic.pk)
            .unread_sequence,
            0,
        )
        subscription = apps.get_model("comics", "Subscription").objects.get(
            user_id=user.pk, comic_id=comic.pk
        )
        self.assertEqual(subscription.pk, kept.pk)
        self.assertEqual(subscription.read_through, 0)

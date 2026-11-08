from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class DistributionMigrationTests(TransactionTestCase):
    migrate_from = [("comics", "0014_alter_comic_last_image")]
    migrate_to = [("comics", "0015_deferred_strip_distribution")]

    def test_historical_strips_and_duplicate_unreads_are_preserved(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        self.addCleanup(self.restore_migrations, latest)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        comic = old_apps.get_model("comics", "Comic").objects.create(name="Historical")
        strip = old_apps.get_model("comics", "Strip").objects.create(
            comic=comic, url="https://example.com/old.png"
        )
        read_strip = old_apps.get_model("comics", "Strip").objects.create(
            comic=comic, url="https://example.com/read.png"
        )
        user = old_apps.get_model("auth", "User").objects.create(username="reader")
        old_unreads = old_apps.get_model("comics", "UnreadStrip").objects
        unread = old_unreads.create(user=user, comic=comic, strip=strip)
        old_unreads.create(user=user, comic=comic, strip=strip)

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        new_apps = executor.loader.project_state(self.migrate_to).apps
        strips = new_apps.get_model("comics", "Strip").objects
        unreads = new_apps.get_model("comics", "UnreadStrip").objects

        self.assertTrue(strips.get(pk=strip.pk).unreads_distributed)
        self.assertTrue(strips.get(pk=read_strip.pk).unreads_distributed)
        self.assertFalse(unreads.filter(strip_id=read_strip.pk).exists())
        self.assertEqual(unreads.count(), 1)
        self.assertTrue(unreads.filter(pk=unread.pk).exists())
        new_strip = strips.create(comic_id=comic.pk, url="https://example.com/new.png")
        self.assertFalse(new_strip.unreads_distributed)

    def restore_migrations(self, targets):
        MigrationExecutor(connection).migrate(targets)

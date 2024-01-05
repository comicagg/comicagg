from django.test import TestCase

from comicagg.accounts.models import User
from comicagg.comics.models import Comic


class UnreadStripTestCase(TestCase):
    fixtures = ["users.json", "comics.json", "strips.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.comic_active = Comic.objects.get(name="Active")
        self.comic_active2 = Comic.objects.get(name="Active2")
        self.comic_ended = Comic.objects.get(name="Ended")
        self.comic_inactive = Comic.objects.get(name="Inactive")
        self.comic_broken = Comic.objects.get(name="Broken")
        self.strip_active = self.comic_active.strip_set.first()
        self.strip_ended = self.comic_ended.strip_set.first()
        self.strip_inactive = self.comic_inactive.strip_set.first()
        self.strip_broken = self.comic_broken.strip_set.first()

    def add_subscriptions(self):
        self.user.subscription_set.create(comic=self.comic_active, position=1)
        self.user.subscription_set.create(comic=self.comic_ended, position=2)
        self.user.subscription_set.create(comic=self.comic_inactive, position=3)
        self.user.subscription_set.create(comic=self.comic_broken, position=4)

    def add_unread_strips(self):
        self.user.unreadstrip_set.create(
            comic=self.comic_active, strip=self.strip_active
        )
        self.user.unreadstrip_set.create(comic=self.comic_ended, strip=self.strip_ended)
        self.user.unreadstrip_set.create(
            comic=self.comic_inactive, strip=self.strip_inactive
        )
        self.user.unreadstrip_set.create(
            comic=self.comic_broken, strip=self.strip_broken
        )

    # ########################
    # #   Test User.strips   #
    # ########################

    def test_strips_no_subscriptions(self):
        """No subscriptions means no unread comics."""
        strips = self.user.unread_strips().count()

        self.assertEqual(strips, 0)

    def test_strips_subscriptions(self):
        """Should return active and ended unreads."""
        self.user.subscription_set.create(comic=self.comic_active)
        self.user.subscription_set.create(comic=self.comic_ended)
        self.user.subscription_set.create(comic=self.comic_inactive)
        self.user.subscription_set.create(comic=self.comic_broken)
        self.user.unreadstrip_set.create(
            comic=self.comic_active, strip=self.strip_active
        )
        self.user.unreadstrip_set.create(comic=self.comic_ended, strip=self.strip_ended)
        self.user.unreadstrip_set.create(
            comic=self.comic_inactive, strip=self.strip_inactive
        )
        self.user.unreadstrip_set.create(
            comic=self.comic_broken, strip=self.strip_broken
        )

        active_subscriptions = self.user.unread_strips().count()

        self.assertEqual(active_subscriptions, 3)

    # ###############################
    # #   Test User.unread_comics   #
    # ###############################

    def test_unread_comics_no_subscriptions(self):
        """Should return an empty list."""
        unreads = self.user.comics_unread()

        self.assertEqual(len(unreads), 0)

    def test_unread_comics_subscriptions(self):
        """Should return an empty list."""
        self.user.subscription_set.create(comic=self.comic_active)
        self.user.subscription_set.create(comic=self.comic_ended)
        self.user.subscription_set.create(comic=self.comic_inactive)
        self.user.subscription_set.create(comic=self.comic_broken)

        unreads = self.user.comics_unread()

        self.assertEqual(len(unreads), 0)

    def test_unread_comics_subscriptions_unreads(self):
        """Should return a non-empty list."""
        self.user.subscription_set.create(comic=self.comic_active)
        self.user.subscription_set.create(comic=self.comic_ended)
        self.user.subscription_set.create(comic=self.comic_inactive)
        self.user.subscription_set.create(comic=self.comic_broken)
        self.user.unreadstrip_set.create(
            comic=self.comic_active, strip=self.strip_active
        )
        self.user.unreadstrip_set.create(comic=self.comic_ended, strip=self.strip_ended)
        self.user.unreadstrip_set.create(
            comic=self.comic_inactive, strip=self.strip_inactive
        )
        self.user.unreadstrip_set.create(
            comic=self.comic_broken, strip=self.strip_broken
        )

        unreads = self.user.comics_unread()

        self.assertEqual(len(unreads), 3)

    # #############################
    # #   Test User.mark_unread   #
    # #############################

    def test_mark_unread_empty(self):
        """Should not change anything since the user is not subscribed."""
        self.user.mark_unread(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_unread_not_subscribed(self):
        """Should not change anything since the user is not subscribed."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_unread(self.comic_active2)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 4)

    def test_mark_unread(self):
        """Should mark the comic as unread."""
        self.add_subscriptions()

        self.user.mark_unread(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 1)

    def test_mark_unread_ended(self):
        """Should mark the comic as unread."""
        self.add_subscriptions()

        self.user.mark_unread(self.comic_ended)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 1)

    def test_mark_unread_broken(self):
        """Should mark the comic as unread."""
        self.add_subscriptions()

        self.user.mark_unread(self.comic_broken)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 1)

    def test_mark_unread_inactive(self):
        """Should not change anything since the comic is inactive."""
        self.add_subscriptions()

        self.user.mark_unread(self.comic_inactive)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_unread_already_unread(self):
        """Should mark the comic as unread."""
        self.add_subscriptions()
        self.user.unreadstrip_set.create(
            comic=self.comic_active, strip=self.strip_active
        )

        self.user.mark_unread(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 1)

    # ###########################
    # #   Test User.mark_read   #
    # ###########################

    def test_mark_read_empty(self):
        """Should not change anything since the user is not subscribed."""
        self.user.mark_read(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_read_not_subscribed(self):
        """Should not change anything since the user is not subscribed."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read(self.comic_active2)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 4)

    def test_mark_read(self):
        """Should mark the comic as read."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 3)

    def test_mark_read_ended(self):
        """Should mark the comic as read."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read(self.comic_ended)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 3)

    def test_mark_read_broken(self):
        """Should mark the comic as read."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read(self.comic_broken)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 3)

    def test_mark_read_inactive(self):
        """Should not change anything since the comic is inactive."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read(self.comic_inactive)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 4)

    def test_mark_read_already_read(self):
        """Should not change anything since the comic is already read."""
        self.add_subscriptions()

        self.user.mark_read(self.comic_active)

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_read_vote_positive(self):
        """Should add a positive vote to the comic."""
        self.add_subscriptions()
        self.add_unread_strips()
        old_comic = Comic.objects.get(pk=self.comic_active.id)

        self.user.mark_read(self.comic_active, 1)

        updated_comic = Comic.objects.get(pk=self.comic_active.id)

        self.assertEqual(updated_comic.total_votes, old_comic.total_votes + 1)
        self.assertEqual(updated_comic.positive_votes, old_comic.positive_votes + 1)

    def test_mark_read_vote_negative(self):
        """Should add a negative vote to the comic."""
        self.add_subscriptions()
        self.add_unread_strips()
        old_comic = Comic.objects.get(pk=self.comic_active.id)

        self.user.mark_read(self.comic_active, -1)

        updated_comic = Comic.objects.get(pk=self.comic_active.id)

        self.assertEqual(updated_comic.total_votes, old_comic.total_votes + 1)
        self.assertEqual(updated_comic.positive_votes, old_comic.positive_votes)

    def test_mark_read_vote_zero(self):
        """Should not add any votes to the comic."""
        self.add_subscriptions()
        self.add_unread_strips()
        old_comic = Comic.objects.get(pk=self.comic_active.id)

        self.user.mark_read(self.comic_active, 0)

        updated_comic = Comic.objects.get(pk=self.comic_active.id)

        self.assertEqual(updated_comic.total_votes, old_comic.total_votes)
        self.assertEqual(updated_comic.positive_votes, old_comic.positive_votes)

    # ###############################
    # #   Test User.mark_read_all   #
    # ###############################

    def test_mark_read_all_empty(self):
        """Should not change anything since the user is not subscribed."""
        self.user.mark_read_all()

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_read_all(self):
        """Should mark all comics as read."""
        self.add_subscriptions()
        self.add_unread_strips()

        self.user.mark_read_all()

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_read_all_already_read(self):
        """Should not change anything since all comics are already read."""
        self.add_subscriptions()

        self.user.mark_read_all()

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

    def test_mark_read_all_mixed(self):
        """Should mark all comics as read."""
        self.add_subscriptions()
        self.add_unread_strips()
        self.user.mark_read(self.comic_active)

        self.user.mark_read_all()

        strip_count = self.user.unreadstrip_set.count()

        self.assertEqual(strip_count, 0)

from django.apps import apps
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse


class DatabaseStatisticsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create(
            username="statistics-admin", is_staff=True, is_superuser=True
        )
        cls.staff = User.objects.create(username="statistics-staff", is_staff=True)
        cls.url = reverse("admin:database_statistics")

    def test_superuser_sees_all_model_tables_in_sorted_order(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/database_statistics.html")
        statistics = response.context["statistics"]
        models = [
            model
            for model in apps.get_models(include_auto_created=True)
            if model._meta.managed and not model._meta.proxy
        ]
        self.assertCountEqual(
            [row["table"] for row in statistics],
            [model._meta.db_table for model in models],
        )
        labels = [row["model"] for row in statistics]
        self.assertEqual(labels, sorted(labels, key=str.lower))
        self.assertNotIn("accounts.User", labels)
        counts = {row["model"]: row["count"] for row in statistics}
        self.assertEqual(counts["auth.User"], 2)
        self.assertEqual(counts["auth.Group"], 0)
        self.assertContains(response, "auth_user")
        self.assertContains(response, "Database statistics")
        self.assertIn("no-cache", response.headers["Cache-Control"])

    def test_counts_refresh_and_include_many_to_many_rows(self):
        self.client.force_login(self.superuser)
        group = Group.objects.create(name="Statistics group")
        self.superuser.groups.add(group)

        response = self.client.get(self.url)
        counts = {row["model"]: row["count"] for row in response.context["statistics"]}
        self.assertEqual(counts["auth.Group"], 1)
        self.assertEqual(counts["auth.User_groups"], 1)

        Group.objects.create(name="Another statistics group")
        response = self.client.get(self.url)
        counts = {row["model"]: row["count"] for row in response.context["statistics"]}
        self.assertEqual(counts["auth.Group"], 2)

    def test_anonymous_user_is_redirected_to_admin_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            f"{reverse('admin:login')}?next={self.url}",
            fetch_redirect_response=False,
        )

    def test_non_staff_and_inactive_superusers_cannot_access(self):
        for flags in (
            {"is_staff": False, "is_active": True},
            {"is_staff": True, "is_active": False},
        ):
            with self.subTest(**flags):
                User.objects.filter(pk=self.superuser.pk).update(**flags)
                self.superuser.refresh_from_db()
                self.client.force_login(self.superuser)

                response = self.client.get(self.url)

                if flags["is_active"]:
                    self.assertEqual(response.status_code, 302)
                else:
                    self.assertEqual(response.status_code, 200)
                    self.assertTemplateUsed(response, "accounts/activate.html")
                self.assertNotIn("statistics", response.context or {})

    def test_staff_without_superuser_status_is_forbidden(self):
        self.client.force_login(self.staff)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_admin_navigation_links_to_statistics_only_for_superusers(self):
        self.client.force_login(self.superuser)
        self.assertContains(
            self.client.get(reverse("admin:index")), f'href="{self.url}"'
        )

        self.client.force_login(self.staff)
        self.assertNotContains(
            self.client.get(reverse("admin:index")), f'href="{self.url}"'
        )

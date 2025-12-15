from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from recipes.models import User
from recipes.tests.helpers import LogInTester


class ToggleUserActiveViewTestCase(TestCase, LogInTester):
    """Tests for the toggle user active status view."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.staff_user = User.objects.create_user(
            username="@admin",
            first_name="Admin",
            last_name="User",
            email="admin@example.org",
            password="Password123",
            is_staff=True,
        )
        self.target_user = User.objects.create_user(
            username="@target",
            first_name="Target",
            last_name="User",
            email="target@example.org",
            password="Password123",
        )
        self.url = reverse(
            "toggle_user_active", kwargs={"user_id": self.target_user.id}
        )

    def test_toggle_active_redirects_anonymous(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/log_in/?next={self.url}")

    def test_toggle_active_redirects_non_staff(self):
        self.client.login(username="@johndoe", password="Password123")
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f"/log_in/?next={self.url}", fetch_redirect_response=False
        )

    def test_staff_can_deactivate_user(self):
        self.client.login(username="@admin", password="Password123")
        self.assertTrue(self.target_user.is_active)

        response = self.client.get(self.url)

        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)
        self.assertRedirects(response, reverse("user_list"))

    def test_staff_can_reactivate_user(self):
        self.client.login(username="@admin", password="Password123")
        self.target_user.is_active = False
        self.target_user.save()

        response = self.client.get(self.url)

        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_active)
        self.assertRedirects(response, reverse("user_list"))

    def test_cannot_deactivate_self(self):
        self.client.login(username="@admin", password="Password123")
        self_url = reverse("toggle_user_active", kwargs={"user_id": self.staff_user.id})

        response = self.client.get(self_url)

        self.staff_user.refresh_from_db()
        self.assertTrue(self.staff_user.is_active)
        self.assertRedirects(response, reverse("user_list"))

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "You cannot deactivate your own account.")

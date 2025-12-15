"""Tests for the edit profile view."""

from django.contrib import messages
from django.test import TestCase
from django.urls import reverse
from recipes.forms import UserForm
from recipes.models import User
from recipes.tests.helpers import LogInTester, reverse_with_next


class EditProfileViewTestCase(TestCase, LogInTester):
    """Test suite for the edit profile view."""

    fixtures = [
        "recipes/tests/fixtures/default_user.json",
        "recipes/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")
        self.url = reverse("edit_profile")
        self.form_input = {
            "first_name": "John2",
            "last_name": "Doe2",
            "username": "@johndoe2",
            "email": "johndoe2@example.org",
            "bio": "Updated bio",
        }

    def test_edit_profile_url(self):
        """Test that the edit profile URL is correct."""
        self.assertEqual(self.url, "/profile/edit/")

    def test_get_edit_profile_redirects_when_not_logged_in(self):
        """Test that accessing edit profile redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertFalse(self._is_logged_in())

    def test_get_edit_profile_when_logged_in(self):
        """Test successful GET request to edit profile when logged in."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_profile.html")

    def test_edit_profile_uses_correct_form(self):
        """Test that edit profile uses UserForm."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(isinstance(form, UserForm))

    def test_edit_profile_form_has_correct_instance(self):
        """Test that the form is bound to the logged-in user."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.instance, self.user)

    def test_edit_profile_form_not_bound_on_get(self):
        """Test that the form is not bound on GET request."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.is_bound)

    def test_successful_profile_update(self):
        """Test successful profile update with valid data."""
        self.client.login(username=self.user.username, password="Password123")
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = User.objects.count()

        # User count should not change (update, not create)
        self.assertEqual(after_count, before_count)

        # Should redirect to dashboard
        response_url = reverse("dashboard")
        self.assertRedirects(
            response, response_url, status_code=302, target_status_code=200
        )
        self.assertTemplateUsed(response, "dashboard.html")

        # Check success message
        messages_list = list(response.context["messages"])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

        # Verify user data was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "@johndoe2")
        self.assertEqual(self.user.first_name, "John2")
        self.assertEqual(self.user.last_name, "Doe2")
        self.assertEqual(self.user.email, "johndoe2@example.org")
        self.assertEqual(self.user.bio, "Updated bio")

    def test_unsuccessful_profile_update_bad_username(self):
        """Test unsuccessful profile update with invalid username."""
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["username"] = "BAD_USERNAME"  # Missing @ symbol
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = User.objects.count()

        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_profile.html")

        form = response.context["form"]
        self.assertTrue(isinstance(form, UserForm))
        self.assertTrue(form.is_bound)

        # Verify user data was not changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "@johndoe")
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")
        self.assertEqual(self.user.email, "johndoe@example.org")

    def test_unsuccessful_profile_update_duplicate_username(self):
        """Test unsuccessful profile update with duplicate username."""
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["username"] = "@janedoe"  # Already exists
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = User.objects.count()

        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_profile.html")

        form = response.context["form"]
        self.assertTrue(isinstance(form, UserForm))
        self.assertTrue(form.is_bound)

        # Verify user data was not changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "@johndoe")
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")
        self.assertEqual(self.user.email, "johndoe@example.org")

    def test_unsuccessful_profile_update_duplicate_email(self):
        """Test unsuccessful profile update with duplicate email."""
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["email"] = "janedoe@example.org"  # Already exists
        before_count = User.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = User.objects.count()

        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_profile.html")

        # Verify user data was not changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "johndoe@example.org")

    def test_unsuccessful_profile_update_invalid_email(self):
        """Test unsuccessful profile update with invalid email format."""
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["email"] = "not_an_email"
        response = self.client.post(self.url, self.form_input)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_profile.html")

        # Verify user data was not changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "johndoe@example.org")

    def test_unsuccessful_profile_update_blank_first_name(self):
        """Test unsuccessful profile update with blank first name."""
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["first_name"] = ""
        response = self.client.post(self.url, self.form_input)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_profile.html")

        # Verify user data was not changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "John")

    def test_unsuccessful_profile_update_blank_last_name(self):
        """Test unsuccessful profile update with blank last name."""
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["last_name"] = ""
        response = self.client.post(self.url, self.form_input)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_profile.html")

        # Verify user data was not changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, "Doe")

    def test_post_edit_profile_redirects_when_not_logged_in(self):
        """Test that POST request redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.post(self.url, self.form_input)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_edit_profile_form_displays_current_values(self):
        """Test that form displays current user values."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Check that current values are displayed
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.email)

    def test_edit_profile_different_user(self):
        """Test that different users can edit their own profiles."""
        self.client.login(username=self.other_user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertEqual(form.instance, self.other_user)
        self.assertContains(response, self.other_user.first_name)

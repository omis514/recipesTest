"""Tests for the remove follower view."""

from django.test import TestCase
from django.urls import reverse
from recipes.models import User, Follow
from recipes.tests.helpers import LogInTester, reverse_with_next


class RemoveFollowerViewTestCase(TestCase, LogInTester):
    """Test suite for the remove follower view."""

    fixtures = [
        "recipes/tests/fixtures/default_user.json",
        "recipes/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")
        self.url = reverse("remove_follower", kwargs={"username": "@janedoe"})
        # Create existing follow relationship (janedoe follows johndoe)
        self.follow = Follow.objects.create(
            follower=self.other_user, following=self.user
        )

    def test_remove_follower_url(self):
        """Test that the remove follower URL is correct."""
        self.assertEqual(self.url, "/profile/remove_follower/@janedoe/")

    def test_remove_follower_redirects_when_not_logged_in(self):
        """Test that removing follower redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_successful_remove_follower(self):
        """Test successfully removing a follower."""
        self.client.login(username=self.user.username, password="Password123")
        before_count = Follow.objects.count()
        response = self.client.get(self.url)
        after_count = Follow.objects.count()

        self.assertEqual(after_count, before_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                follower=self.other_user, following=self.user
            ).exists()
        )

    def test_remove_follower_not_following_you(self):
        """Test removing a user who isn't following you."""
        self.follow.delete()  # Remove the follow first
        self.client.login(username=self.user.username, password="Password123")
        before_count = Follow.objects.count()
        response = self.client.get(self.url)
        after_count = Follow.objects.count()

        self.assertEqual(after_count, before_count)

    def test_remove_nonexistent_follower_returns_404(self):
        """Test that removing a nonexistent user returns 404."""
        self.client.login(username=self.user.username, password="Password123")
        url = reverse("remove_follower", kwargs={"username": "@nonexistent"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_remove_follower_redirects_to_referer(self):
        """Test that remove follower redirects back to the referring page."""
        self.client.login(username=self.user.username, password="Password123")
        referer = reverse("user_profile")
        response = self.client.get(self.url, HTTP_REFERER=referer)
        self.assertRedirects(response, referer, fetch_redirect_response=False)

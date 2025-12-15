"""Tests for the unfollow user view."""

from django.test import TestCase
from django.urls import reverse
from recipes.models import User, Follow
from recipes.tests.helpers import LogInTester, reverse_with_next


class UnfollowUserViewTestCase(TestCase, LogInTester):
    """Test suite for the unfollow user view."""

    fixtures = [
        "recipes/tests/fixtures/default_user.json",
        "recipes/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")
        self.url = reverse("unfollow_user", kwargs={"username": "@janedoe"})
        # Create existing follow relationship
        self.follow = Follow.objects.create(
            follower=self.user, following=self.other_user
        )

    def test_unfollow_user_url(self):
        """Test that the unfollow user URL is correct."""
        self.assertEqual(self.url, "/unfollow/@janedoe/")

    def test_unfollow_user_redirects_when_not_logged_in(self):
        """Test that unfollowing redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_successful_unfollow(self):
        """Test successfully unfollowing a user."""
        self.client.login(username=self.user.username, password="Password123")
        before_count = Follow.objects.count()
        response = self.client.get(self.url)
        after_count = Follow.objects.count()

        self.assertEqual(after_count, before_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                follower=self.user, following=self.other_user
            ).exists()
        )

    def test_unfollow_user_not_following(self):
        """Test unfollowing a user you're not following."""
        self.follow.delete()  # Remove the follow first
        self.client.login(username=self.user.username, password="Password123")
        before_count = Follow.objects.count()
        response = self.client.get(self.url)
        after_count = Follow.objects.count()

        self.assertEqual(after_count, before_count)

    def test_unfollow_nonexistent_user_returns_404(self):
        """Test that unfollowing a nonexistent user returns 404."""
        self.client.login(username=self.user.username, password="Password123")
        url = reverse("unfollow_user", kwargs={"username": "@nonexistent"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_unfollow_redirects_to_referer(self):
        """Test that unfollow redirects back to the referring page."""
        self.client.login(username=self.user.username, password="Password123")
        referer = reverse("user_profile")
        response = self.client.get(self.url, HTTP_REFERER=referer)
        self.assertRedirects(response, referer, fetch_redirect_response=False)

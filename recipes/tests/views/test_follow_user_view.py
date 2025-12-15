"""Tests for the follow user view."""

from django.test import TestCase
from django.urls import reverse
from recipes.models import User, Follow
from recipes.tests.helpers import LogInTester, reverse_with_next


class FollowUserViewTestCase(TestCase, LogInTester):
    """Test suite for the follow user view."""

    fixtures = [
        "recipes/tests/fixtures/default_user.json",
        "recipes/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")
        self.url = reverse("follow_user", kwargs={"username": "@janedoe"})

    def test_follow_user_url(self):
        """Test that the follow user URL is correct."""
        self.assertEqual(self.url, "/follow/@janedoe/")

    def test_follow_user_redirects_when_not_logged_in(self):
        """Test that following redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_successful_follow(self):
        """Test successfully following another user."""
        self.client.login(username=self.user.username, password="Password123")
        before_count = Follow.objects.count()
        response = self.client.get(self.url)
        after_count = Follow.objects.count()

        self.assertEqual(after_count, before_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                follower=self.user, following=self.other_user
            ).exists()
        )

    def test_cannot_follow_yourself(self):
        """Test that a user cannot follow themselves."""
        self.client.login(username=self.user.username, password="Password123")
        url = reverse("follow_user", kwargs={"username": "@johndoe"})
        before_count = Follow.objects.count()
        response = self.client.get(url)
        after_count = Follow.objects.count()

        self.assertEqual(after_count, before_count)

    def test_cannot_follow_same_user_twice(self):
        """Test that duplicate follows are prevented."""
        Follow.objects.create(follower=self.user, following=self.other_user)
        self.client.login(username=self.user.username, password="Password123")
        before_count = Follow.objects.count()
        response = self.client.get(self.url)
        after_count = Follow.objects.count()

        self.assertEqual(after_count, before_count)

    def test_follow_nonexistent_user_returns_404(self):
        """Test that following a nonexistent user returns 404."""
        self.client.login(username=self.user.username, password="Password123")
        url = reverse("follow_user", kwargs={"username": "@nonexistent"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_follow_redirects_to_referer(self):
        """Test that follow redirects back to the referring page."""
        self.client.login(username=self.user.username, password="Password123")
        referer = reverse("search_users")
        response = self.client.get(self.url, HTTP_REFERER=referer)
        self.assertRedirects(response, referer, fetch_redirect_response=False)

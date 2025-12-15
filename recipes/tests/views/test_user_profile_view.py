"""Tests for the user profile view."""

from django.test import TestCase
from django.urls import reverse
from recipes.forms import UserForm
from recipes.models import User, Follow, Recipe
from recipes.tests.helpers import LogInTester, reverse_with_next


class UserProfileViewTestCase(TestCase, LogInTester):
    """Test suite for the user profile view."""

    fixtures = [
        "recipes/tests/fixtures/default_user.json",
        "recipes/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")
        self.url = reverse("user_profile")

    def test_user_profile_url(self):
        """Test that the user profile URL is correct."""
        self.assertEqual(self.url, "/profile/view/self/")

    def test_get_user_profile_redirects_when_not_logged_in(self):
        """Test that accessing user profile redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertFalse(self._is_logged_in())

    def test_user_profile_with_no_followers_or_following(self):
        """Test user profile when user has no followers or following."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        following_relations = response.context["following_relations"]
        followers_relations = response.context["followers_relations"]
        self.assertEqual(len(following_relations), 0)
        self.assertEqual(len(followers_relations), 0)

    def test_user_profile_displays_followers(self):
        """Test user profile with multiple followers."""
        petra = User.objects.get(username="@petrapickles")
        peter = User.objects.get(username="@peterpickles")

        # Multiple users follow johndoe
        Follow.objects.create(follower=self.other_user, following=self.user)
        Follow.objects.create(follower=petra, following=self.user)
        Follow.objects.create(follower=peter, following=self.user)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        followers_relations = response.context["followers_relations"]
        self.assertEqual(len(followers_relations), 3)

    def test_user_profile_displays_following(self):
        """Test user profile when following multiple users."""
        petra = User.objects.get(username="@petrapickles")
        peter = User.objects.get(username="@peterpickles")

        # johndoe follows multiple users
        Follow.objects.create(follower=self.user, following=self.other_user)
        Follow.objects.create(follower=self.user, following=petra)
        Follow.objects.create(follower=self.user, following=peter)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        following_relations = response.context["following_relations"]
        self.assertEqual(len(following_relations), 3)

    def test_user_profile_following_uses_select_related(self):
        """Test that following_relations uses select_related for efficiency."""
        Follow.objects.create(follower=self.user, following=self.other_user)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        following_relations = response.context["following_relations"]
        # Access related user without additional queries (select_related works)
        with self.assertNumQueries(0):
            _ = following_relations[0].following.username

    def test_user_profile_followers_uses_select_related(self):
        """Test that followers_relations uses select_related for efficiency."""
        Follow.objects.create(follower=self.other_user, following=self.user)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        followers_relations = response.context["followers_relations"]
        # Access related user without additional queries (select_related works)
        with self.assertNumQueries(0):
            _ = followers_relations[0].follower.username

    def test_user_profile_displays_user_info(self):
        """Test that user profile displays correct user information."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Check user info is in response content
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.email)

    def test_user_profile_returns_logged_in_users_profile(self):
        """Test that user profile returns the profile of the logged-in user."""
        # Login as janedoe instead
        self.client.login(username=self.other_user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertEqual(form.instance, self.other_user)
        self.assertContains(response, self.other_user.first_name)
        self.assertContains(response, self.other_user.username)

    def test_user_profile_context_contains_user_recipes(self):
        """Test that user profile context contains user_recipes."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("user_recipes", response.context)

    def test_user_profile_displays_own_recipes(self):
        """Test that user profile displays the logged-in user's recipes."""
        # Create recipes for johndoe
        recipe1 = Recipe.objects.create(
            author=self.user,
            title="John's Recipe 1",
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
            time=30,
        )
        recipe2 = Recipe.objects.create(
            author=self.user,
            title="John's Recipe 2",
            difficulty=Recipe.Difficulty.MEDIUM,
            spiciness=Recipe.Spiciness.MILD,
            cuisine=Recipe.Cuisine.ITALIAN,
            time=45,
        )
        # Create a recipe for another user (should NOT appear)
        Recipe.objects.create(
            author=self.other_user,
            title="Jane's Recipe",
            difficulty=Recipe.Difficulty.HARD,
            spiciness=Recipe.Spiciness.HOT,
            cuisine=Recipe.Cuisine.MEXICAN,
            time=60,
        )

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        user_recipes = response.context["user_recipes"]
        self.assertEqual(len(user_recipes), 2)
        self.assertIn(recipe1, user_recipes)
        self.assertIn(recipe2, user_recipes)

    def test_user_profile_with_no_recipes(self):
        """Test user profile when user has no recipes."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        user_recipes = response.context["user_recipes"]
        self.assertEqual(len(user_recipes), 0)

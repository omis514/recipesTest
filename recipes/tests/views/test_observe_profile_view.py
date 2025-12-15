"""Tests for the observe profile view (viewing another user's profile)."""

from django.test import TestCase
from django.urls import reverse
from recipes.models import User, Follow, Recipe
from recipes.tests.helpers import LogInTester, reverse_with_next


class ObserveProfileViewTestCase(TestCase, LogInTester):
    """Test suite for the observe profile view."""

    fixtures = [
        "recipes/tests/fixtures/default_user.json",
        "recipes/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")
        self.petra = User.objects.get(username="@petrapickles")
        self.url = reverse("observe_profile", kwargs={"username": "@janedoe"})

    def test_observe_profile_url(self):
        """Test that the observe profile URL is correct."""
        self.assertEqual(self.url, "/profile/view/@janedoe/")

    def test_get_observe_profile_redirects_when_not_logged_in(self):
        """Test that accessing observe profile redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertFalse(self._is_logged_in())

    def test_get_observe_profile_when_logged_in(self):
        """Test successful GET request to observe profile when logged in."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "observe_user.html")

    def test_observe_profile_redirects_to_own_profile_when_viewing_self(self):
        """Test that viewing your own profile redirects to user_profile."""
        self.client.login(username=self.user.username, password="Password123")
        url = reverse("observe_profile", kwargs={"username": "@johndoe"})
        response = self.client.get(url)
        self.assertRedirects(
            response, reverse("user_profile"), status_code=302, target_status_code=200
        )

    def test_observe_profile_returns_404_for_nonexistent_user(self):
        """Test that observing a nonexistent user returns 404."""
        self.client.login(username=self.user.username, password="Password123")
        url = reverse("observe_profile", kwargs={"username": "@nonexistentuser"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_observe_profile_context_contains_target_user(self):
        """Test that observe profile context contains target_user."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("target_user", response.context)
        self.assertEqual(response.context["target_user"], self.other_user)

    def test_observe_profile_target_user_is_correct(self):
        """Test that the correct target user is returned."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        target_user = response.context["target_user"]
        self.assertEqual(target_user.username, "@janedoe")
        self.assertEqual(target_user.first_name, "Jane")
        self.assertEqual(target_user.last_name, "Doe")

    def test_observe_profile_displays_target_user_info(self):
        """Test that target user's information is displayed."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, self.other_user.first_name)
        self.assertContains(response, self.other_user.last_name)
        self.assertContains(response, self.other_user.username)
        self.assertContains(response, self.other_user.email)

    def test_observe_profile_is_followed_false_when_not_following(self):
        """Test that is_followed is False when not following the user."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        target_user = response.context["target_user"]
        self.assertFalse(target_user.is_followed)

    def test_observe_profile_is_followed_true_when_following(self):
        """Test that is_followed is True when following the user."""
        # Create follow relationship: johndoe follows janedoe
        Follow.objects.create(follower=self.user, following=self.other_user)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        target_user = response.context["target_user"]
        self.assertTrue(target_user.is_followed)

    def test_observe_profile_is_followed_considers_only_current_user(self):
        """Test that is_followed only considers the current user's follows."""
        # Petra follows janedoe, but johndoe does not
        Follow.objects.create(follower=self.petra, following=self.other_user)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        target_user = response.context["target_user"]
        # johndoe is not following janedoe, so is_followed should be False
        self.assertFalse(target_user.is_followed)

    def test_observe_profile_as_different_logged_in_user(self):
        """Test that different logged-in users see correct is_followed status."""
        # johndoe follows janedoe
        Follow.objects.create(follower=self.user, following=self.other_user)

        # Login as johndoe - should see is_followed=True
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertTrue(response.context["target_user"].is_followed)

        # Login as petra - should see is_followed=False
        self.client.login(username=self.petra.username, password="Password123")
        response = self.client.get(self.url)
        self.assertFalse(response.context["target_user"].is_followed)

    def test_observe_profile_url_with_special_characters(self):
        """Test that usernames with @ symbol work correctly in URL."""
        self.client.login(username=self.user.username, password="Password123")
        # The URL already has @ in it
        url = reverse("observe_profile", kwargs={"username": "@petrapickles"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["target_user"].username, "@petrapickles")

    def test_observe_profile_redirects_self_view_for_any_user(self):
        """Test that any user viewing their own profile gets redirected."""
        # Login as janedoe and try to view janedoe's profile
        self.client.login(username=self.other_user.username, password="Password123")
        url = reverse("observe_profile", kwargs={"username": "@janedoe"})
        response = self.client.get(url)
        self.assertRedirects(
            response, reverse("user_profile"), status_code=302, target_status_code=200
        )

    def test_observe_profile_post_redirects_when_not_logged_in(self):
        """Test that POST request redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.post(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_observe_profile_context_contains_user_recipes(self):
        """Test that observe profile context contains user_recipes."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("user_recipes", response.context)

    def test_observe_profile_displays_target_user_recipes(self):
        """Test that observe profile displays the target user's recipes."""
        # Create recipes for janedoe (target user)
        recipe1 = Recipe.objects.create(
            author=self.other_user,
            title="Jane's Recipe 1",
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
            time=30,
        )
        recipe2 = Recipe.objects.create(
            author=self.other_user,
            title="Jane's Recipe 2",
            difficulty=Recipe.Difficulty.MEDIUM,
            spiciness=Recipe.Spiciness.MILD,
            cuisine=Recipe.Cuisine.ITALIAN,
            time=45,
        )
        # Create a recipe for johndoe (should NOT appear)
        Recipe.objects.create(
            author=self.user,
            title="John's Recipe",
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

    def test_observe_profile_with_no_recipes(self):
        """Test observe profile when target user has no recipes."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        user_recipes = response.context["user_recipes"]
        self.assertEqual(len(user_recipes), 0)

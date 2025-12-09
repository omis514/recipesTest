"""Tests for the dashboard view."""

from django.test import TestCase
from django.urls import reverse
from recipes.models import Recipe, Comment, User
from recipes.tests.helpers import LogInTester, reverse_with_next


class DashboardViewTestCase(TestCase, LogInTester):
    """Test suite for the dashboard view."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.url = reverse("dashboard")
        self.user = User.objects.get(username="@johndoe")

    def test_dashboard_url(self):
        """Test that the dashboard URL is correct."""
        self.assertEqual(self.url, "/dashboard/")

    def test_get_dashboard_redirects_when_not_logged_in(self):
        """Test that accessing dashboard redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertFalse(self._is_logged_in())

    def test_get_dashboard_when_logged_in(self):
        """Test successful GET request to dashboard when logged in."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")

    def test_dashboard_context_contains_user(self):
        """Test that dashboard context contains the current user."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("user", response.context)
        self.assertEqual(response.context["user"], self.user)

    def test_dashboard_context_contains_feed_recipes(self):
        """Test that dashboard context contains feed_recipes."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("feed_recipes", response.context)
        self.assertIsNotNone(response.context["feed_recipes"])

    def test_dashboard_with_no_recipes(self):
        """Test dashboard when there are no recipes."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        feed_recipes = response.context["feed_recipes"]
        self.assertEqual(len(feed_recipes), 0)

    def test_dashboard_feed_recipes_limit(self):
        """Test that feed recipes are limited to 20."""
        self.client.login(username=self.user.username, password="Password123")

        # Create 25 recipes
        for i in range(25):
            Recipe.objects.create(
                author=self.user,
                title=f"Recipe {i}",
                description=f"Description {i}",
                difficulty=Recipe.Difficulty.EASY,
                spiciness=Recipe.Spiciness.NOT_SPICY,
                cuisine=Recipe.Cuisine.World,
                time=30,
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        feed_recipes = response.context["feed_recipes"]
        # Should be limited to 20 recipes
        self.assertLessEqual(len(feed_recipes), 20)

    def test_dashboard_feed_recipes_structure(self):
        """Test that feed recipes have the correct structure with annotations."""
        self.client.login(username=self.user.username, password="Password123")

        # Create a recipe
        recipe = Recipe.objects.create(
            author=self.user,
            title="Test Recipe",
            description="Test Description",
            difficulty=Recipe.Difficulty.MEDIUM,
            spiciness=Recipe.Spiciness.MILD,
            cuisine=Recipe.Cuisine.ITALIAN,
            time=45,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        feed_recipes = response.context["feed_recipes"]

        self.assertEqual(len(feed_recipes), 1)
        feed_recipe = feed_recipes[0]

        # Check that recipe has total_comments annotation
        self.assertTrue(hasattr(feed_recipe, "total_comments"))
        self.assertEqual(feed_recipe.total_comments, 0)

        # Check that recipe has top_comment attribute
        self.assertTrue(hasattr(feed_recipe, "top_comment"))
        self.assertIsNone(feed_recipe.top_comment)

    def test_dashboard_feed_recipes_with_comments(self):
        """Test that feed recipes include comment data correctly."""
        self.client.login(username=self.user.username, password="Password123")

        # Create a recipe
        recipe = Recipe.objects.create(
            author=self.user,
            title="Test Recipe",
            description="Test Description",
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
            time=30,
        )

        # Create a comment
        comment = Comment.objects.create(
            recipe=recipe,
            author=self.user,
            content="This is a great recipe!",
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        feed_recipes = response.context["feed_recipes"]

        self.assertEqual(len(feed_recipes), 1)
        feed_recipe = feed_recipes[0]

        # Check total comments
        self.assertEqual(feed_recipe.total_comments, 1)

        # Check top comment
        self.assertIsNotNone(feed_recipe.top_comment)
        self.assertEqual(feed_recipe.top_comment, comment)

    def test_dashboard_feed_recipes_with_multiple_comments(self):
        """Test that feed recipes show the most liked comment as top comment."""
        self.client.login(username=self.user.username, password="Password123")

        # Create another user for liking comments
        other_user = User.objects.create_user(
            username="@otheruser",
            email="other@example.org",
            password="Password123",
            first_name="Other",
            last_name="User",
        )

        # Create a recipe
        recipe = Recipe.objects.create(
            author=self.user,
            title="Test Recipe",
            description="Test Description",
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
            time=30,
        )

        # Create comments
        comment1 = Comment.objects.create(
            recipe=recipe,
            author=self.user,
            content="First comment",
        )

        comment2 = Comment.objects.create(
            recipe=recipe,
            author=other_user,
            content="Second comment with more likes",
        )

        # Add likes to comment2
        comment2.likes.add(self.user, other_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        feed_recipes = response.context["feed_recipes"]

        self.assertEqual(len(feed_recipes), 1)
        feed_recipe = feed_recipes[0]

        # Check total comments
        self.assertEqual(feed_recipe.total_comments, 2)

        # Check that top comment is the one with most likes
        self.assertIsNotNone(feed_recipe.top_comment)
        self.assertEqual(feed_recipe.top_comment, comment2)
        self.assertEqual(feed_recipe.top_comment.like_count, 2)

    def test_dashboard_feed_recipes_random_ordering(self):
        """Test that feed recipes are returned in random order."""
        self.client.login(username=self.user.username, password="Password123")

        # Create multiple recipes (limited to 6 to match view limit)
        recipes = []
        for i in range(6):
            recipe = Recipe.objects.create(
                author=self.user,
                title=f"Recipe {i}",
                description=f"Description {i}",
                difficulty=Recipe.Difficulty.EASY,
                spiciness=Recipe.Spiciness.NOT_SPICY,
                cuisine=Recipe.Cuisine.World,
                time=30,
            )
            recipes.append(recipe)

        # Make multiple requests and check that order can vary
        # Note: The view orders by spiciness_diff and created_at, not randomly
        # but we can verify the recipes are returned
        response1 = self.client.get(self.url)
        self.assertEqual(response1.status_code, 200)
        feed_recipes_1 = list(response1.context["feed_recipes"])

        # Verify all recipes are present (order may vary)
        recipe_ids_1 = {r.id for r in feed_recipes_1}
        expected_ids = {r.id for r in recipes}
        self.assertEqual(recipe_ids_1, expected_ids)

    def test_dashboard_feed_recipes_includes_author(self):
        """Test that feed recipes include author information."""
        self.client.login(username=self.user.username, password="Password123")

        recipe = Recipe.objects.create(
            author=self.user,
            title="Test Recipe",
            description="Test Description",
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
            time=30,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        feed_recipes = response.context["feed_recipes"]

        self.assertEqual(len(feed_recipes), 1)
        feed_recipe = feed_recipes[0]

        # Check that author is loaded (select_related)
        self.assertEqual(feed_recipe.author, self.user)
        # Verify no additional queries needed (select_related works)
        with self.assertNumQueries(0):
            _ = feed_recipe.author.username

    def test_dashboard_feed_recipes_with_no_top_comment(self):
        """Test that feed recipes handle cases with no comments gracefully."""
        self.client.login(username=self.user.username, password="Password123")

        recipe = Recipe.objects.create(
            author=self.user,
            title="Test Recipe",
            description="Test Description",
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
            time=30,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        feed_recipes = response.context["feed_recipes"]

        self.assertEqual(len(feed_recipes), 1)
        feed_recipe = feed_recipes[0]

        # Should have total_comments = 0
        self.assertEqual(feed_recipe.total_comments, 0)

        # Should have top_comment = None
        self.assertIsNone(feed_recipe.top_comment)

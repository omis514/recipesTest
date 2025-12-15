"""Tests for the recipe list view."""

from django.test import TestCase
from django.urls import reverse
from recipes.models import Recipe, User, Comment, Rating
from recipes.tests.helpers import LogInTester


class RecipeListViewTestCase(TestCase, LogInTester):
    """Tests for the recipe list view."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.create_user(
            username="@janedoe",
            first_name="Jane",
            last_name="Doe",
            email="jane@example.org",
            password="Password123",
        )
        # Create public recipes
        self.recipe1 = Recipe.objects.create(
            author=self.user,
            title="Recipe One",
            description="First recipe",
            time=30,
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.MILD,
            cuisine=Recipe.Cuisine.ITALIAN,
            visibility=Recipe.Visibility.PUBLIC,
        )
        self.recipe2 = Recipe.objects.create(
            author=self.other_user,
            title="Recipe Two",
            description="Second recipe",
            time=45,
            difficulty=Recipe.Difficulty.MEDIUM,
            spiciness=Recipe.Spiciness.MEDIUM,
            cuisine=Recipe.Cuisine.MEXICAN,
            visibility=Recipe.Visibility.PUBLIC,
        )
        self.recipe3 = Recipe.objects.create(
            author=self.user,
            title="Recipe Three",
            description="Third recipe",
            time=60,
            difficulty=Recipe.Difficulty.HARD,
            spiciness=Recipe.Spiciness.HOT,
            cuisine=Recipe.Cuisine.Chinese,
            visibility=Recipe.Visibility.PUBLIC,
        )
        # Create private recipe
        self.private_recipe = Recipe.objects.create(
            author=self.user,
            title="Private Recipe",
            description="Private recipe",
            time=20,
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
            visibility=Recipe.Visibility.PRIVATE,
        )
        self.url = reverse("recipe_list")

    def test_recipe_list_url(self):
        """Test that the URL is correct."""
        self.assertEqual(self.url, "/recipes/")

    def test_recipe_list_requires_login(self):
        """Test that recipe list requires login."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/log_in/?next={self.url}")

    def test_recipe_list_accessible_when_logged_in(self):
        """Test that logged-in users can access recipe list."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_list.html")

    def test_recipe_list_shows_public_recipes(self):
        """Test that public recipes are shown."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        self.assertIn(self.recipe1, recipes)
        self.assertIn(self.recipe2, recipes)
        self.assertIn(self.recipe3, recipes)

    def test_recipe_list_shows_own_private_recipes(self):
        """Test that users can see their own private recipes."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        self.assertIn(self.private_recipe, recipes)

    def test_recipe_list_hides_others_private_recipes(self):
        """Test that users cannot see others' private recipes."""
        self.client.login(username=self.other_user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        self.assertNotIn(self.private_recipe, recipes)

    def test_recipe_list_default_sort_newest(self):
        """Test that recipes are sorted by newest by default."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        # Newest first (recipe3 was created last, private_recipe was created after recipe3)
        # Check that recipe3 comes before recipe2, and recipe2 comes before recipe1
        recipe3_index = recipes.index(self.recipe3)
        recipe2_index = recipes.index(self.recipe2)
        recipe1_index = recipes.index(self.recipe1)
        self.assertLess(recipe3_index, recipe2_index)
        self.assertLess(recipe2_index, recipe1_index)

    def test_recipe_list_sort_oldest(self):
        """Test that recipes can be sorted by oldest."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"sort": "oldest"})
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        # Oldest first - check that recipe1 comes before recipe2, and recipe2 comes before recipe3
        recipe1_index = recipes.index(self.recipe1)
        recipe2_index = recipes.index(self.recipe2)
        recipe3_index = recipes.index(self.recipe3)
        self.assertLess(recipe1_index, recipe2_index)
        self.assertLess(recipe2_index, recipe3_index)

    def test_recipe_list_sort_popular(self):
        """Test that recipes can be sorted by popularity (most comments)."""
        # Add comments to recipes
        Comment.objects.create(
            recipe=self.recipe1, author=self.user, content="Comment 1"
        )
        Comment.objects.create(
            recipe=self.recipe1, author=self.other_user, content="Comment 2"
        )
        Comment.objects.create(
            recipe=self.recipe2, author=self.user, content="Comment 3"
        )

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"sort": "popular"})
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        # Most commented first
        self.assertEqual(recipes[0], self.recipe1)  # 2 comments
        self.assertEqual(recipes[1], self.recipe2)  # 1 comment

    def test_recipe_list_sort_rating(self):
        """Test that recipes can be sorted by rating."""
        # Add ratings
        Rating.objects.create(recipe=self.recipe1, user=self.user, rating=5)
        Rating.objects.create(recipe=self.recipe1, user=self.other_user, rating=5)
        Rating.objects.create(recipe=self.recipe2, user=self.user, rating=3)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"sort": "rating"})
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        # Highest rated first
        self.assertEqual(recipes[0], self.recipe1)  # 5.0 average
        self.assertEqual(recipes[1], self.recipe2)  # 3.0 average

    def test_recipe_list_filter_by_difficulty(self):
        """Test that recipes can be filtered by difficulty."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"difficulty": Recipe.Difficulty.EASY})
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        # Should only show easy recipes
        self.assertIn(self.recipe1, recipes)
        self.assertNotIn(self.recipe2, recipes)  # Medium
        self.assertNotIn(self.recipe3, recipes)  # Hard

    def test_recipe_list_filter_by_spiciness(self):
        """Test that recipes can be filtered by spiciness."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"spiciness": Recipe.Spiciness.MILD})
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        # Should only show mild recipes
        self.assertIn(self.recipe1, recipes)
        self.assertNotIn(self.recipe2, recipes)  # Medium
        self.assertNotIn(self.recipe3, recipes)  # Hot

    def test_recipe_list_filter_by_cuisine(self):
        """Test that recipes can be filtered by cuisine."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"cuisine": Recipe.Cuisine.ITALIAN})
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        # Should only show Italian recipes
        self.assertIn(self.recipe1, recipes)
        self.assertNotIn(self.recipe2, recipes)  # Mexican
        self.assertNotIn(self.recipe3, recipes)  # Chinese

    def test_recipe_list_search_by_title(self):
        """Test that recipes can be searched by title."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "One"})
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        self.assertIn(self.recipe1, recipes)
        self.assertNotIn(self.recipe2, recipes)
        self.assertNotIn(self.recipe3, recipes)

    def test_recipe_list_search_by_description(self):
        """Test that recipes can be searched by description."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "Second"})
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        self.assertNotIn(self.recipe1, recipes)
        self.assertIn(self.recipe2, recipes)
        self.assertNotIn(self.recipe3, recipes)

    def test_recipe_list_search_case_insensitive(self):
        """Test that search is case insensitive."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "recipe"})
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        # Should find all recipes with "recipe" in title or description
        self.assertGreater(len(recipes), 0)

    def test_recipe_list_combined_filters(self):
        """Test that multiple filters can be combined."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(
            self.url,
            {
                "difficulty": Recipe.Difficulty.EASY,
                "spiciness": Recipe.Spiciness.MILD,
                "cuisine": Recipe.Cuisine.ITALIAN,
            },
        )
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        # Should only show recipe1 (matches all filters)
        self.assertIn(self.recipe1, recipes)
        self.assertNotIn(self.recipe2, recipes)
        self.assertNotIn(self.recipe3, recipes)

    def test_recipe_list_pagination(self):
        """Test that pagination works."""
        # Create more than 12 recipes (pagination limit)
        for i in range(15):
            Recipe.objects.create(
                author=self.user,
                title=f"Recipe {i}",
                description=f"Recipe {i} description",
                time=30,
                difficulty=Recipe.Difficulty.EASY,
                spiciness=Recipe.Spiciness.NOT_SPICY,
                cuisine=Recipe.Cuisine.World,
                visibility=Recipe.Visibility.PUBLIC,
            )

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Should have pagination
        self.assertIn("page_obj", response.context)
        # First page should have 12 recipes
        self.assertEqual(len(response.context["page_obj"]), 12)
        self.assertTrue(response.context["page_obj"].has_next())

    def test_recipe_list_second_page(self):
        """Test accessing the second page."""
        # Create more than 12 recipes
        for i in range(15):
            Recipe.objects.create(
                author=self.user,
                title=f"Recipe {i}",
                description=f"Recipe {i} description",
                time=30,
                difficulty=Recipe.Difficulty.EASY,
                spiciness=Recipe.Spiciness.NOT_SPICY,
                cuisine=Recipe.Cuisine.World,
                visibility=Recipe.Visibility.PUBLIC,
            )

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"page": 2})
        self.assertEqual(response.status_code, 200)
        # Second page should have remaining recipes
        self.assertGreater(len(response.context["page_obj"]), 0)
        self.assertTrue(response.context["page_obj"].has_previous())

    def test_recipe_list_shows_top_comment(self):
        """Test that top comment (most liked) is shown for each recipe."""
        # Create comments with different like counts
        comment1 = Comment.objects.create(
            recipe=self.recipe1, author=self.user, content="Comment 1"
        )
        comment2 = Comment.objects.create(
            recipe=self.recipe1, author=self.other_user, content="Comment 2"
        )
        # Add more likes to comment2
        comment2.likes.add(self.user, self.other_user)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        recipe1_in_list = next(r for r in recipes if r.pk == self.recipe1.pk)
        # Top comment should be comment2 (most likes)
        self.assertEqual(recipe1_in_list.top_comment, comment2)

    def test_recipe_list_shows_favorite_status(self):
        """Test that favorite status is shown for each recipe."""
        # Add recipe to favorites
        self.recipe1.favorites.add(self.user)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        recipe1_in_list = next(r for r in recipes if r.pk == self.recipe1.pk)
        self.assertTrue(recipe1_in_list.is_favorited)

    def test_recipe_list_shows_average_rating(self):
        """Test that average rating is calculated and shown."""
        # Add ratings
        Rating.objects.create(recipe=self.recipe1, user=self.user, rating=5)
        Rating.objects.create(recipe=self.recipe1, user=self.other_user, rating=3)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        recipes = list(response.context["recipes"])
        recipe1_in_list = next(r for r in recipes if r.pk == self.recipe1.pk)
        self.assertEqual(recipe1_in_list.average_rating, 4.0)
        self.assertEqual(recipe1_in_list.rating_count, 2)

    def test_recipe_list_context_variables(self):
        """Test that all context variables are present."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIn("page_obj", context)
        self.assertIn("recipes", context)
        self.assertIn("difficulties", context)
        self.assertIn("spicinesses", context)
        self.assertIn("cuisines", context)
        self.assertIn("sort_by", context)

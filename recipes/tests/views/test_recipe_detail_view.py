"""Tests for the recipe detail view."""

from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from recipes.models import (
    Recipe,
    User,
    Comment,
    Rating,
    Ingredient,
    Instruction,
    Follow,
)
from recipes.tests.helpers import LogInTester


class RecipeDetailViewTestCase(TestCase, LogInTester):
    """Tests for the recipe detail view."""

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
        self.recipe = Recipe.objects.create(
            author=self.user,
            title="Test Recipe",
            description="A delicious test recipe.",
            time=30,
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.MILD,
            cuisine=Recipe.Cuisine.World,
            visibility=Recipe.Visibility.PUBLIC,
        )
        self.private_recipe = Recipe.objects.create(
            author=self.user,
            title="Private Recipe",
            description="A private recipe.",
            time=45,
            difficulty=Recipe.Difficulty.MEDIUM,
            spiciness=Recipe.Spiciness.MEDIUM,
            cuisine=Recipe.Cuisine.ITALIAN,
            visibility=Recipe.Visibility.PRIVATE,
        )
        # Add ingredients and instructions
        Ingredient.objects.create(
            recipe=self.recipe, name="Sugar", quantity=100, unit="g"
        )
        Ingredient.objects.create(
            recipe=self.recipe, name="Flour", quantity=200, unit="g"
        )
        Instruction.objects.create(
            recipe=self.recipe, step=1, description="Mix ingredients"
        )
        Instruction.objects.create(
            recipe=self.recipe, step=2, description="Bake for 30 minutes"
        )
        self.url = reverse("recipe_detail", kwargs={"pk": self.recipe.pk})

    def test_recipe_detail_url(self):
        """Test that the URL is correct."""
        self.assertEqual(self.url, f"/recipes/{self.recipe.pk}/")

    def test_recipe_detail_accessible_public_recipe(self):
        """Test that public recipes are accessible to everyone."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_detail.html")
        self.assertEqual(response.context["recipe"], self.recipe)

    def test_recipe_detail_shows_ingredients(self):
        """Test that ingredients are displayed."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        ingredients = list(response.context["recipe"].ingredients.all())
        self.assertEqual(len(ingredients), 2)
        self.assertEqual(ingredients[0].name, "Sugar")
        self.assertEqual(ingredients[1].name, "Flour")

    def test_recipe_detail_shows_instructions_ordered(self):
        """Test that instructions are displayed in order."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        instructions = list(response.context["recipe"].instructions.all())
        self.assertEqual(len(instructions), 2)
        self.assertEqual(instructions[0].step, 1)
        self.assertEqual(instructions[1].step, 2)

    def test_recipe_detail_private_recipe_author(self):
        """Test that recipe author can view their private recipe."""
        self.client.login(username=self.user.username, password="Password123")
        url = reverse("recipe_detail", kwargs={"pk": self.private_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["recipe"], self.private_recipe)

    def test_recipe_detail_private_recipe_anonymous(self):
        """Test that anonymous users cannot view private recipes."""
        url = reverse("recipe_detail", kwargs={"pk": self.private_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_recipe_detail_private_recipe_other_user(self):
        """Test that other users cannot view private recipes."""
        self.client.login(username=self.other_user.username, password="Password123")
        url = reverse("recipe_detail", kwargs={"pk": self.private_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_recipe_detail_not_found(self):
        """Test that 404 is returned for non-existent recipe."""
        url = reverse("recipe_detail", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_recipe_detail_rating_display(self):
        """Test that ratings are displayed correctly."""
        # Create ratings
        Rating.objects.create(recipe=self.recipe, user=self.user, rating=5)
        Rating.objects.create(recipe=self.recipe, user=self.other_user, rating=3)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        recipe = response.context["recipe"]
        self.assertEqual(recipe.average_rating, 4.0)
        self.assertEqual(recipe.rating_count, 2)

    def test_recipe_detail_no_ratings(self):
        """Test that recipe with no ratings shows 0."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        recipe = response.context["recipe"]
        self.assertEqual(recipe.average_rating, 0)
        self.assertEqual(recipe.rating_count, 0)

    def test_recipe_detail_user_rating_score_authenticated(self):
        """Test that authenticated user sees their rating."""
        Rating.objects.create(recipe=self.recipe, user=self.user, rating=4)
        self.client.login(username=self.user.username, password="Password123")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user_rating_score"], 4)

    def test_recipe_detail_user_rating_score_unauthenticated(self):
        """Test that unauthenticated user sees 0 rating."""
        Rating.objects.create(recipe=self.recipe, user=self.user, rating=4)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user_rating_score"], 0)

    def test_recipe_detail_user_rating_score_no_rating(self):
        """Test that user with no rating sees 0."""
        self.client.login(username=self.user.username, password="Password123")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user_rating_score"], 0)

    def test_recipe_detail_comments_display(self):
        """Test that comments are displayed."""
        comment1 = Comment.objects.create(
            recipe=self.recipe, author=self.user, content="Great recipe!"
        )
        comment2 = Comment.objects.create(
            recipe=self.recipe, author=self.other_user, content="Love it!"
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        comments = list(response.context["comments"])
        self.assertEqual(len(comments), 2)

    def test_recipe_detail_comments_sort_newest(self):
        """Test that comments are sorted by newest by default."""
        comment1 = Comment.objects.create(
            recipe=self.recipe, author=self.user, content="First comment"
        )
        comment2 = Comment.objects.create(
            recipe=self.recipe, author=self.other_user, content="Second comment"
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        comments = list(response.context["comments"])
        # Newest first
        self.assertEqual(comments[0].content, "Second comment")
        self.assertEqual(comments[1].content, "First comment")

    def test_recipe_detail_comments_sort_top(self):
        """Test that comments can be sorted by top (most likes)."""
        comment1 = Comment.objects.create(
            recipe=self.recipe, author=self.user, content="First comment"
        )
        comment2 = Comment.objects.create(
            recipe=self.recipe, author=self.other_user, content="Second comment"
        )
        # Add likes to comment1
        comment1.likes.add(self.other_user)

        response = self.client.get(self.url, {"sort": "top"})
        self.assertEqual(response.status_code, 200)
        comments = list(response.context["comments"])
        # Most liked first
        self.assertEqual(comments[0].content, "First comment")
        self.assertEqual(comments[1].content, "Second comment")

    def test_recipe_detail_comments_sort_oldest(self):
        """Test that comments can be sorted by oldest."""
        comment1 = Comment.objects.create(
            recipe=self.recipe, author=self.user, content="First comment"
        )
        comment2 = Comment.objects.create(
            recipe=self.recipe, author=self.other_user, content="Second comment"
        )

        response = self.client.get(self.url, {"sort": "oldest"})
        self.assertEqual(response.status_code, 200)
        comments = list(response.context["comments"])
        # Oldest first
        self.assertEqual(comments[0].content, "First comment")
        self.assertEqual(comments[1].content, "Second comment")

    def test_recipe_detail_only_top_level_comments(self):
        """Test that only top-level comments are shown (not replies)."""
        parent_comment = Comment.objects.create(
            recipe=self.recipe, author=self.user, content="Parent comment"
        )
        reply = Comment.objects.create(
            recipe=self.recipe,
            author=self.other_user,
            content="Reply comment",
            parent_comment=parent_comment,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        comments = list(response.context["comments"])
        # Only parent comment should be shown
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].content, "Parent comment")

    def test_recipe_detail_is_following_author_authenticated(self):
        """Test that authenticated user sees if they follow the author."""
        # User follows other_user
        Follow.objects.create(follower=self.user, following=self.other_user)
        # Create recipe by other_user
        other_recipe = Recipe.objects.create(
            author=self.other_user,
            title="Other Recipe",
            description="Another recipe.",
            time=20,
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
        )

        self.client.login(username=self.user.username, password="Password123")
        url = reverse("recipe_detail", kwargs={"pk": other_recipe.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_following_author"])

    def test_recipe_detail_is_following_author_not_following(self):
        """Test that user sees False when not following author."""
        # Create recipe by other_user
        other_recipe = Recipe.objects.create(
            author=self.other_user,
            title="Other Recipe",
            description="Another recipe.",
            time=20,
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
        )

        self.client.login(username=self.user.username, password="Password123")
        url = reverse("recipe_detail", kwargs={"pk": other_recipe.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_following_author"])

    def test_recipe_detail_is_following_author_unauthenticated(self):
        """Test that unauthenticated user sees False for following status."""
        # Create recipe by other_user
        other_recipe = Recipe.objects.create(
            author=self.other_user,
            title="Other Recipe",
            description="Another recipe.",
            time=20,
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
        )

        url = reverse("recipe_detail", kwargs={"pk": other_recipe.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_following_author"])

    def test_recipe_detail_is_following_author_own_recipe(self):
        """Test that user sees False when viewing their own recipe."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_following_author"])

"""Tests for the delete recipe view."""

from django.contrib import messages
from django.test import TestCase
from django.urls import reverse
from recipes.models import Recipe, Ingredient, Instruction, User
from recipes.tests.helpers import LogInTester, reverse_with_next


class DeleteRecipeViewTestCase(TestCase, LogInTester):
    """Test suite for the delete recipe view."""

    fixtures = [
        "recipes/tests/fixtures/default_user.json",
        "recipes/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")

        # Create a recipe owned by johndoe
        self.recipe = Recipe.objects.create(
            author=self.user,
            title="Recipe To Delete",
            description="A recipe that will be deleted",
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
            vegetarian=False,
            time=30,
        )

        # Create related objects to test cascade delete
        Ingredient.objects.create(
            recipe=self.recipe,
            name="Test Ingredient",
            quantity=1,
            unit="cup",
        )
        Instruction.objects.create(
            recipe=self.recipe,
            step=1,
            description="Test instruction.",
        )

        self.url = reverse("delete_recipe", kwargs={"pk": self.recipe.pk})

    def test_delete_recipe_url(self):
        """Test that the delete recipe URL is correct."""
        self.assertEqual(self.url, f"/recipes/{self.recipe.pk}/delete/")

    def test_get_delete_recipe_redirects_when_not_logged_in(self):
        """Test that GET request redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertFalse(self._is_logged_in())

    def test_post_delete_recipe_redirects_when_not_logged_in(self):
        """Test that POST request redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.post(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_get_delete_recipe_redirects_to_detail(self):
        """Test that GET request redirects to recipe detail (POST required)."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, follow=True)

        redirect_url = reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        self.assertRedirects(response, redirect_url)

        # Recipe should still exist
        self.assertTrue(Recipe.objects.filter(pk=self.recipe.pk).exists())

    def test_successful_delete_full_integration(self):
        """Test full delete flow: DB update, Cascade, Redirect, and Message."""
        self.client.login(username=self.user.username, password="Password123")

        # Verify related objects exist before we start (sanity check)
        self.assertTrue(Ingredient.objects.filter(recipe=self.recipe).exists())
        self.assertTrue(Instruction.objects.filter(recipe=self.recipe).exists())

        before_count = Recipe.objects.count()
        response = self.client.post(self.url, follow=True)
        after_count = Recipe.objects.count()

        self.assertEqual(after_count, before_count - 1)
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())
        self.assertRedirects(response, reverse("recipe_list"))

        # Check Messages
        messages_list = list(response.context["messages"])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].level, messages.SUCCESS)
        self.assertIn("Recipe To Delete", str(messages_list[0]))

        # Check Cascading Delete (Ingredients/Instructions)
        self.assertFalse(Ingredient.objects.filter(recipe=self.recipe).exists())
        self.assertFalse(Instruction.objects.filter(recipe=self.recipe).exists())

    def test_non_author_cannot_delete_recipe(self):
        """Test that non-author cannot delete another user's recipe."""
        self.client.login(username=self.other_user.username, password="Password123")
        before_count = Recipe.objects.count()
        response = self.client.post(self.url, follow=True)
        after_count = Recipe.objects.count()

        # Recipe should still exist
        self.assertEqual(after_count, before_count)
        self.assertTrue(Recipe.objects.filter(pk=self.recipe.pk).exists())

        # Should redirect to recipe detail
        redirect_url = reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        self.assertRedirects(response, redirect_url)

        # Should show error message
        messages_list = list(response.context["messages"])
        self.assertEqual(messages_list[0].level, messages.ERROR)

    def test_staff_can_delete_any_recipe(self):
        """Test that staff can delete any recipe."""
        self.other_user.is_staff = True
        self.other_user.save()

        self.client.login(username=self.other_user.username, password="Password123")
        before_count = Recipe.objects.count()
        response = self.client.post(self.url, follow=True)
        after_count = Recipe.objects.count()

        self.assertEqual(after_count, before_count - 1)
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())
        self.assertRedirects(response, reverse("recipe_list"))

    def test_delete_nonexistent_recipe_returns_404(self):
        """Test that deleting a nonexistent recipe returns 404."""
        self.client.login(username=self.user.username, password="Password123")
        url = reverse("delete_recipe", kwargs={"pk": 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

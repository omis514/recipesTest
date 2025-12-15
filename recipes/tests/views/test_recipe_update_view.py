"""Tests of the recipe update view."""

from django.test import TestCase
from django.urls import reverse

from recipes.models import Recipe, User
from recipes.tests.helpers import LogInTester


class RecipeUpdateViewTestCase(TestCase, LogInTester):
    """Tests of the recipe update view."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.client.force_login(self.user)
        self.recipe = Recipe.objects.create(
            author=self.user,
            title="Update Test Recipe",
            description="Original description",
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
            time=30,
            visibility=Recipe.Visibility.PUBLIC,
        )
        self.url = reverse("edit_recipe", kwargs={"pk": self.recipe.pk})
        self.form_input = {
            "title": "Updated Title",
            "description": "Updated description",
            "difficulty": Recipe.Difficulty.MEDIUM,
            "spiciness": Recipe.Spiciness.HOT,
            "cuisine": Recipe.Cuisine.ITALIAN,
            "vegetarian": True,
            "time": 45,
            "visibility": Recipe.Visibility.PRIVATE,
            "ingredients-TOTAL_FORMS": "1",
            "ingredients-INITIAL_FORMS": "0",
            "ingredients-MIN_NUM_FORMS": "1",
            "ingredients-MAX_NUM_FORMS": "1000",
            "ingredients-0-name": "Updated Ingredient",
            "ingredients-0-quantity": "2",
            "ingredients-0-unit": "kg",
            "instructions-TOTAL_FORMS": "1",
            "instructions-INITIAL_FORMS": "0",
            "instructions-MIN_NUM_FORMS": "1",
            "instructions-MAX_NUM_FORMS": "1000",
            "instructions-0-step": "1",
            "instructions-0-description": "Updated step",
        }

    def test_update_recipe_visibility(self):
        """Test that author can update recipe visibility."""
        response = self.client.post(self.url, self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.visibility, Recipe.Visibility.PRIVATE)
        self.assertEqual(self.recipe.title, "Updated Title")

    def test_edit_page_renders_visibility_field(self):
        """Test that the edit page renders the visibility field."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="visibility"')
        self.assertContains(response, 'option value="1"')  # 1 is private option

    def test_detail_page_edit_button_presence(self):
        """Test that edit button appears for author but not for others."""
        detail_url = reverse("recipe_detail", kwargs={"pk": self.recipe.pk})

        # Author should see edit button
        response = self.client.get(detail_url)
        self.assertContains(response, "Edit Recipe")
        self.assertContains(response, self.url)

        # Other user should not see edit button
        other_user = User.objects.create_user(username="other", password="password")
        self.client.force_login(other_user)
        response = self.client.get(detail_url)
        self.assertNotContains(response, "Edit Recipe")
        self.assertNotContains(response, self.url)

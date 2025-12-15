"""Tests for the edit recipe view."""

from django.contrib import messages
from django.test import TestCase
from django.urls import reverse
from recipes.forms import RecipeForm
from recipes.models import Recipe, Ingredient, Instruction, User
from recipes.tests.helpers import LogInTester, reverse_with_next


class EditRecipeViewTestCase(TestCase, LogInTester):
    """Test suite for the edit recipe view (RecipeUpdateView)."""

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
            title="Original Recipe",
            description="Original description",
            difficulty=Recipe.Difficulty.EASY,
            spiciness=Recipe.Spiciness.NOT_SPICY,
            cuisine=Recipe.Cuisine.World,
            vegetarian=False,
            time=30,
        )

        # Create an ingredient for the recipe
        self.ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            name="Original Ingredient",
            quantity=1,
            unit="cup",
        )

        # Create an instruction for the recipe
        self.instruction = Instruction.objects.create(
            recipe=self.recipe,
            step=1,
            description="Original instruction step.",
        )

        self.url = reverse("edit_recipe", kwargs={"pk": self.recipe.pk})
        self.form_input = {
            "title": "Updated Recipe",
            "description": "Updated description",
            "difficulty": Recipe.Difficulty.MEDIUM,
            "spiciness": Recipe.Spiciness.MILD,
            "cuisine": Recipe.Cuisine.ITALIAN,
            "vegetarian": True,
            "visibility": Recipe.Visibility.PUBLIC,
            "time": "60",
            "ingredients-TOTAL_FORMS": "1",
            "ingredients-INITIAL_FORMS": "1",
            "ingredients-MIN_NUM_FORMS": "1",
            "ingredients-MAX_NUM_FORMS": "1000",
            "ingredients-0-id": str(self.ingredient.id),
            "ingredients-0-name": "Updated Ingredient",
            "ingredients-0-quantity": "2",
            "ingredients-0-unit": "tbsp",
            "instructions-TOTAL_FORMS": "1",
            "instructions-INITIAL_FORMS": "1",
            "instructions-MIN_NUM_FORMS": "1",
            "instructions-MAX_NUM_FORMS": "1000",
            "instructions-0-id": str(self.instruction.id),
            "instructions-0-step": "1",
            "instructions-0-description": "Updated instruction step.",
        }

    def test_edit_recipe_url(self):
        """Test that the edit recipe URL is correct."""
        self.assertEqual(self.url, f"/recipes/{self.recipe.pk}/edit/")

    def test_get_edit_recipe_redirects_when_not_logged_in(self):
        """Test that accessing edit recipe redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertFalse(self._is_logged_in())

    def test_get_edit_recipe_when_logged_in_as_author(self):
        """Test successful GET request to edit recipe when logged in as author."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_edit.html")

    def test_get_edit_recipe_forbidden_for_non_author(self):
        """Test that non-author cannot access edit page."""
        self.client.login(username=self.other_user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_edit_recipe_allowed_for_staff(self):
        """Test that staff can access edit page for any recipe."""
        self.other_user.is_staff = True
        self.other_user.save()
        self.client.login(username=self.other_user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_edit.html")

    def test_edit_recipe_uses_correct_form(self):
        """Test that edit recipe uses RecipeForm."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(isinstance(form, RecipeForm))

    def test_edit_recipe_form_has_correct_instance(self):
        """Test that the form is bound to the correct recipe."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.instance, self.recipe)

    def test_edit_recipe_context_contains_formsets(self):
        """Test that context contains ingredient and instruction formsets."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ingredient_formset", response.context)
        self.assertIn("instruction_formset", response.context)

    def test_edit_recipe_displays_existing_data(self):
        """Test that form displays existing recipe values."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recipe.title)
        self.assertContains(response, self.ingredient.name)
        self.assertContains(response, self.instruction.description)

    def test_successful_full_update(self):
        """Test successful update of recipe, ingredients, and instructions."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url, self.form_input, follow=True)

        # Check Redirection and Messages
        self.assertRedirects(
            response, reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        )
        messages_list = list(response.context["messages"])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

        # Check Recipe Fields
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, "Updated Recipe")
        self.assertEqual(self.recipe.author, self.user)  # checks security here

        # Check Ingredients
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.name, "Updated Ingredient")

        # Check Instructions
        self.instruction.refresh_from_db()
        self.assertEqual(self.instruction.description, "Updated instruction step.")

    def test_successful_recipe_update_shows_success_message(self):
        """Test that successful update shows success message."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url, self.form_input, follow=True)

        messages_list = list(response.context["messages"])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

    def test_unsuccessful_recipe_update_with_invalid_title(self):
        """Test unsuccessful update with blank title."""
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["title"] = ""
        response = self.client.post(self.url, self.form_input)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_edit.html")

        # Verify recipe data was not changed
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, "Original Recipe")

    def test_unsuccessful_recipe_update_with_invalid_ingredient(self):
        """Test unsuccessful update with invalid ingredient."""
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["ingredients-0-name"] = ""
        response = self.client.post(self.url, self.form_input)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_edit.html")

        # Verify ingredient was not changed
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.name, "Original Ingredient")

    def test_unsuccessful_recipe_update_with_invalid_instruction(self):
        """Test unsuccessful update with invalid instruction."""
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["instructions-0-description"] = ""
        response = self.client.post(self.url, self.form_input)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_edit.html")

        # Verify instruction was not changed
        self.instruction.refresh_from_db()
        self.assertEqual(self.instruction.description, "Original instruction step.")

    def test_post_edit_recipe_redirects_when_not_logged_in(self):
        """Test that POST request redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.post(self.url, self.form_input)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )

    def test_post_edit_recipe_forbidden_for_non_author(self):
        """Test that non-author cannot POST to edit page."""
        self.client.login(username=self.other_user.username, password="Password123")
        response = self.client.post(self.url, self.form_input)
        self.assertEqual(response.status_code, 403)

        # Verify recipe was not changed
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.title, "Original Recipe")

    def test_edit_nonexistent_recipe_returns_404(self):
        """Test that editing a nonexistent recipe returns 404."""
        self.client.login(username=self.user.username, password="Password123")
        url = reverse("edit_recipe", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_recipe_author_unchanged_after_update(self):
        """Test that recipe author is not changed after update."""
        self.client.login(username=self.user.username, password="Password123")
        self.client.post(self.url, self.form_input, follow=True)

        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.author, self.user)

"""Tests of the recipe create view."""

from django.contrib import messages
from django.test import TestCase
from django.urls import reverse
from recipes.forms import RecipeForm
from recipes.models import Recipe, Ingredient, Instruction, User
from recipes.tests.helpers import LogInTester


class RecipeCreateViewTestCase(TestCase, LogInTester):
    """Tests of the recipe create view."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.url = reverse("recipe_create")
        self.user = User.objects.get(username="@johndoe")
        self.form_input = {
            "title": "Test Recipe",
            "description": "A test recipe description",
            "difficulty": Recipe.Difficulty.EASY,
            "time": "45",
            "ingredients-TOTAL_FORMS": "1",
            "ingredients-INITIAL_FORMS": "0",
            "ingredients-MIN_NUM_FORMS": "1",
            "ingredients-MAX_NUM_FORMS": "1000",
            "ingredients-0-name": "Rice",
            "ingredients-0-quantity": "1",
            "ingredients-0-unit": "cup",
            "instructions-TOTAL_FORMS": "1",
            "instructions-INITIAL_FORMS": "0",
            "instructions-MIN_NUM_FORMS": "1",
            "instructions-MAX_NUM_FORMS": "1000",
            "instructions-0-step": "1",
            "instructions-0-description": "First, prepare the ingredients.",
        }

    def test_recipe_create_url(self):
        self.assertEqual(self.url, "/recipe/create/")

    def test_get_recipe_create_redirects_when_not_logged_in(self):
        response = self.client.get(self.url, follow=True)
        redirect_url = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertFalse(self._is_logged_in())

    def test_get_recipe_create_when_logged_in(self):
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_create.html")
        form = response.context["form"]
        self.assertTrue(isinstance(form, RecipeForm))
        self.assertFalse(form.is_bound)
        self.assertIn("ingredient_formset", response.context)
        self.assertIn("instruction_formset", response.context)

    def test_post_recipe_create_redirects_when_not_logged_in(self):
        response = self.client.post(self.url, self.form_input, follow=True)
        redirect_url = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertFalse(self._is_logged_in())

    def test_successful_recipe_create(self):
        self.client.login(username=self.user.username, password="Password123")
        before_recipe_count = Recipe.objects.count()
        before_ingredient_count = Ingredient.objects.count()
        before_instruction_count = Instruction.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_recipe_count = Recipe.objects.count()
        after_ingredient_count = Ingredient.objects.count()
        after_instruction_count = Instruction.objects.count()

        self.assertEqual(after_recipe_count, before_recipe_count + 1)
        self.assertEqual(after_ingredient_count, before_ingredient_count + 1)
        self.assertEqual(after_instruction_count, before_instruction_count + 1)

        redirect_url = reverse("dashboard")
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertTemplateUsed(response, "dashboard.html")

        recipe = Recipe.objects.get(title="Test Recipe")
        self.assertEqual(recipe.author, self.user)
        self.assertEqual(recipe.description, "A test recipe description")
        self.assertEqual(recipe.difficulty, Recipe.Difficulty.EASY)
        self.assertEqual(recipe.time, 45)

        ingredient = recipe.ingredients.first()
        self.assertEqual(ingredient.name, "Rice")
        self.assertEqual(ingredient.quantity, 1)
        self.assertEqual(ingredient.unit, "cup")

        instruction = recipe.instructions.first()
        self.assertEqual(instruction.step, 1)
        self.assertEqual(instruction.description, "First, prepare the ingredients.")

        messages_list = list(response.context["messages"])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(messages_list[0].level, messages.SUCCESS)
        self.assertEqual(str(messages_list[0]), "Recipe created!")

    def test_unsuccessful_recipe_create_with_invalid_recipe_form(self):
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["title"] = ""  # Invalid - title is required
        before_count = Recipe.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = Recipe.objects.count()

        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_create.html")
        form = response.context["form"]
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())

    def test_unsuccessful_recipe_create_with_invalid_ingredient_formset(self):
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["ingredients-0-name"] = ""  # Invalid - name is required
        before_count = Recipe.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = Recipe.objects.count()

        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_create.html")
        ingredient_formset = response.context["ingredient_formset"]
        self.assertFalse(ingredient_formset.is_valid())

    def test_unsuccessful_recipe_create_with_invalid_instruction_formset(self):
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["instructions-0-description"] = (
            ""  # Invalid - description is required
        )
        before_count = Recipe.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = Recipe.objects.count()

        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_create.html")
        instruction_formset = response.context["instruction_formset"]
        self.assertFalse(instruction_formset.is_valid())

    def test_recipe_create_with_multiple_ingredients(self):
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["ingredients-TOTAL_FORMS"] = "2"
        self.form_input["ingredients-1-name"] = "Chicken"
        self.form_input["ingredients-1-quantity"] = "500"
        self.form_input["ingredients-1-unit"] = "g"

        before_ingredient_count = Ingredient.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_ingredient_count = Ingredient.objects.count()

        self.assertEqual(after_ingredient_count, before_ingredient_count + 2)

        recipe = Recipe.objects.get(title="Test Recipe")
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertEqual(ingredients[0].name, "Rice")
        self.assertEqual(ingredients[1].name, "Chicken")

    def test_recipe_create_with_multiple_instructions(self):
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["instructions-TOTAL_FORMS"] = "2"
        self.form_input["instructions-1-step"] = "2"
        self.form_input["instructions-1-description"] = "Second, cook the rice."

        before_instruction_count = Instruction.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_instruction_count = Instruction.objects.count()

        self.assertEqual(after_instruction_count, before_instruction_count + 2)

        recipe = Recipe.objects.get(title="Test Recipe")
        instructions = recipe.instructions.all().order_by("step")
        self.assertEqual(instructions.count(), 2)
        self.assertEqual(instructions[0].step, 1)
        self.assertEqual(instructions[1].step, 2)

    def test_recipe_create_minimum_one_ingredient_required(self):
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["ingredients-TOTAL_FORMS"] = "1"
        self.form_input["ingredients-0-name"] = ""
        self.form_input["ingredients-0-quantity"] = ""
        self.form_input["ingredients-0-unit"] = ""

        before_count = Recipe.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = Recipe.objects.count()

        self.assertEqual(after_count, before_count)
        ingredient_formset = response.context["ingredient_formset"]
        self.assertFalse(ingredient_formset.is_valid())

    def test_recipe_create_minimum_one_instruction_required(self):
        self.client.login(username=self.user.username, password="Password123")
        self.form_input["instructions-TOTAL_FORMS"] = "1"
        self.form_input["instructions-0-step"] = ""
        self.form_input["instructions-0-description"] = ""

        before_count = Recipe.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = Recipe.objects.count()

        self.assertEqual(after_count, before_count)
        instruction_formset = response.context["instruction_formset"]
        self.assertFalse(instruction_formset.is_valid())

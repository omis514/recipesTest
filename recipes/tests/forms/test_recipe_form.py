"""Unit tests of the recipe form."""

from django import forms
from django.test import TestCase
from recipes.forms import RecipeForm
from recipes.models import Recipe, User


class RecipeFormTestCase(TestCase):
    """Unit tests of the recipe form."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.author = User.objects.get(username="@johndoe")
        self.form_input = {
            "title": "Test Recipe",
            "description": "A test recipe description",
            "difficulty": Recipe.Difficulty.EASY,
            "time": 45,
        }

    def test_form_has_necessary_fields(self):
        form = RecipeForm()
        self.assertIn("title", form.fields)
        self.assertIn("description", form.fields)
        self.assertIn("difficulty", form.fields)
        self.assertIn("time", form.fields)

    def test_form_title_field_is_char_field(self):
        form = RecipeForm()
        self.assertTrue(isinstance(form.fields["title"], forms.CharField))

    def test_form_description_field_is_char_field(self):
        form = RecipeForm()
        self.assertTrue(isinstance(form.fields["description"], forms.CharField))

    def test_form_difficulty_field_is_choice_field(self):
        form = RecipeForm()
        # ModelForm with IntegerField choices becomes TypedChoiceField
        self.assertTrue(
            isinstance(
                form.fields["difficulty"],
                (forms.TypedChoiceField, forms.ChoiceField, forms.IntegerField),
            )
        )

    def test_form_time_field_is_integer_field(self):
        form = RecipeForm()
        self.assertTrue(isinstance(form.fields["time"], forms.IntegerField))

    def test_valid_recipe_form(self):
        form = RecipeForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_title_is_required(self):
        self.form_input["title"] = ""
        form = RecipeForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_form_title_can_be_100_chars(self):
        self.form_input["title"] = "x" * 100
        form = RecipeForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_title_cannot_be_over_100_chars(self):
        self.form_input["title"] = "x" * 101
        form = RecipeForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_form_description_can_be_blank(self):
        self.form_input["description"] = ""
        form = RecipeForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_difficulty_is_required(self):
        self.form_input["difficulty"] = ""
        form = RecipeForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn("difficulty", form.errors)

    def test_form_difficulty_can_be_easy(self):
        self.form_input["difficulty"] = Recipe.Difficulty.EASY
        form = RecipeForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_difficulty_can_be_medium(self):
        self.form_input["difficulty"] = Recipe.Difficulty.MEDIUM
        form = RecipeForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_difficulty_can_be_hard(self):
        self.form_input["difficulty"] = Recipe.Difficulty.HARD
        form = RecipeForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_difficulty_cannot_be_invalid_choice(self):
        self.form_input["difficulty"] = 4
        form = RecipeForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn("difficulty", form.errors)

    def test_form_must_save_correctly(self):
        form = RecipeForm(data=self.form_input)
        self.assertTrue(form.is_valid())
        recipe = form.save(commit=False)
        recipe.author = self.author
        recipe.save()
        self.assertEqual(recipe.title, "Test Recipe")
        self.assertEqual(recipe.description, "A test recipe description")
        self.assertEqual(recipe.difficulty, Recipe.Difficulty.EASY)
        self.assertEqual(recipe.time, 45)

    def test_form_uses_model_validation(self):
        # Title that's too long
        self.form_input["title"] = "x" * 101
        form = RecipeForm(data=self.form_input)
        self.assertFalse(form.is_valid())

"""Unit tests for the Recipe model."""

from django.core.exceptions import ValidationError
from django.test import TestCase
from recipes.models import Recipe, User, Ingredient, Instruction
import time


class RecipeModelTestCase(TestCase):

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.author = User.objects.get(username="@johndoe")
        self.recipe = Recipe.objects.create(
            author=self.author,
            title="Test Title",
            description="Test Description",
            difficulty=Recipe.Difficulty.EASY,
            time=45,
        )

    def test_valid_recipe(self):
        self._assert_recipe_is_valid()

    def test_author_cannot_be_null(self):
        self.recipe.author = None
        self._assert_recipe_is_invalid()

    def test_recipe_deleted_when_author_deleted(self):
        before_count = Recipe.objects.count()
        self.author.delete()
        after_count = Recipe.objects.count()
        self.assertEqual(after_count, before_count - 1)

    def test_title_cannot_be_blank(self):
        self.recipe.title = ""
        self._assert_recipe_is_invalid()

    def test_title_can_be_100_chars(self):
        self.recipe.title = "x" * 100
        self._assert_recipe_is_valid()

    def test_title_cannot_be_over_100_chars(self):
        self.recipe.title = "x" * 101
        self._assert_recipe_is_invalid()

    def test_description_can_be_blank(self):
        self.recipe.description = ""
        self._assert_recipe_is_valid()

    def test_default_difficulty_is_easy(self):
        new_recipe = Recipe.objects.create(
            author=self.author,
            title="Test Recipe 2",
        )
        self.assertEqual(new_recipe.difficulty, Recipe.Difficulty.EASY)

    def test_difficulty_must_be_in_choices(self):
        self.recipe.difficulty = 4
        self._assert_recipe_is_invalid()

    def test_difficulty_can_be_1(self):
        self.recipe.difficulty = 1
        self._assert_recipe_is_valid()

    def test_difficulty_can_be_3(self):
        self.recipe.difficulty = 3
        self._assert_recipe_is_valid()

    def test_image_can_be_blank(self):
        self.recipe.image = None
        self._assert_recipe_is_valid()

    def test_recipe_can_have_multiple_instructions(self):
        self.assertEqual(self.recipe.instructions.count(), 0)
        Instruction.objects.create(
            recipe=self.recipe, step=1, description="Test description"
        )
        Instruction.objects.create(
            recipe=self.recipe, step=2, description="Test description 2"
        )
        self.assertEqual(self.recipe.instructions.count(), 2)

        instruction_list = self.recipe.instructions.all()
        self.assertEqual(str(instruction_list[0]), "Instruction 1 for Test Title")
        self.assertEqual(str(instruction_list[1]), "Instruction 2 for Test Title")

    def test_recipe_can_have_multiple_ingredients(self):
        self.assertEqual(self.recipe.ingredients.count(), 0)
        Ingredient.objects.create(
            recipe=self.recipe, name="Rice", quantity=1, unit="cup"
        )
        Ingredient.objects.create(
            recipe=self.recipe, name="Chicken Breast", quantity=1, unit=""
        )
        self.assertEqual(self.recipe.ingredients.count(), 2)

        ingredient_list = self.recipe.ingredients.all()
        self.assertEqual(str(ingredient_list[0]), "1 cup Rice")
        self.assertEqual(str(ingredient_list[1]), "1 Chicken Breast")

    def test_time_cannot_be_null(self):
        self.recipe.time = None
        self._assert_recipe_is_invalid()

    def test_time_can_be_zero(self):
        self.recipe.time = 0
        self._assert_recipe_is_valid()

    def test_time_display_under_60(self):
        self.recipe.time = 30
        self.assertEqual(self.recipe.get_time(), "30 mins")

    def test_time_display_at_zero(self):
        self.recipe.time = 0
        self.assertEqual(self.recipe.get_time(), "0 mins")

    def test_time_display_above_60(self):
        self.recipe.time = 90
        self.assertEqual(self.recipe.get_time(), "1.5 hrs")

    def test_time_display_at_60(self):
        self.recipe.time = 60
        self.assertEqual(self.recipe.get_time(), "1.0 hrs")

    def test_time_display_complex_decimal(self):
        self.recipe.time = 73
        self.assertEqual(self.recipe.get_time(), "1.2 hrs")

    def test_recipe_can_have_favorites(self):
        self.recipe.favorites.add(self.author)
        self.assertEqual(self.recipe.favorites.count(), 1)
        self.assertEqual(self.recipe.favorites.first(), self.author)

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.recipe.created_at)

    def test_default_ordering_is_by_newest(self):
        time.sleep(0.01)

        new_recipe = Recipe.objects.create(
            author=self.author,
            title="Test Recipe 2",
        )
        recipes = Recipe.objects.all()
        self.assertEqual(recipes.first(), new_recipe)
        self.assertEqual(recipes.last(), self.recipe)

    def test_str_returns_title(self):
        self.assertEqual(str(self.recipe), "Test Title")

    def test_default_spiciness_is_not_spicy(self):
        new_recipe = Recipe.objects.create(
            author=self.author,
            title="Test Recipe 2",
        )
        self.assertEqual(new_recipe.spiciness, Recipe.Spiciness.NOT_SPICY)

    def test_spiciness_must_be_in_choices(self):
        self.recipe.spiciness = 10
        self._assert_recipe_is_invalid()

    def test_spiciness_can_be_not_spicy(self):
        self.recipe.spiciness = Recipe.Spiciness.NOT_SPICY
        self._assert_recipe_is_valid()

    def test_spiciness_can_be_mild(self):
        self.recipe.spiciness = Recipe.Spiciness.MILD
        self._assert_recipe_is_valid()

    def test_spiciness_can_be_medium(self):
        self.recipe.spiciness = Recipe.Spiciness.MEDIUM
        self._assert_recipe_is_valid()

    def test_spiciness_can_be_hot(self):
        self.recipe.spiciness = Recipe.Spiciness.HOT
        self._assert_recipe_is_valid()

    def test_spiciness_can_be_very_hot(self):
        self.recipe.spiciness = Recipe.Spiciness.VERY_HOT
        self._assert_recipe_is_valid()

    def test_default_cuisine_is_world(self):
        new_recipe = Recipe.objects.create(
            author=self.author,
            title="Test Recipe 2",
        )
        self.assertEqual(new_recipe.cuisine, Recipe.Cuisine.World)

    def test_cuisine_must_be_in_choices(self):
        self.recipe.cuisine = 100
        self._assert_recipe_is_invalid()

    def test_cuisine_can_be_world(self):
        self.recipe.cuisine = Recipe.Cuisine.World
        self._assert_recipe_is_valid()

    def test_cuisine_can_be_british(self):
        self.recipe.cuisine = Recipe.Cuisine.BRITISH
        self._assert_recipe_is_valid()

    def test_cuisine_can_be_italian(self):
        self.recipe.cuisine = Recipe.Cuisine.ITALIAN
        self._assert_recipe_is_valid()

    def test_cuisine_can_be_chinese(self):
        self.recipe.cuisine = Recipe.Cuisine.Chinese
        self._assert_recipe_is_valid()

    def test_cuisine_can_be_japanese(self):
        self.recipe.cuisine = Recipe.Cuisine.Japanese
        self._assert_recipe_is_valid()

    def test_cuisine_can_be_indian(self):
        self.recipe.cuisine = Recipe.Cuisine.Indian
        self._assert_recipe_is_valid()

    def test_default_vegetarian_is_false(self):
        new_recipe = Recipe.objects.create(
            author=self.author,
            title="Test Recipe 2",
        )
        self.assertFalse(new_recipe.vegetarian)

    def test_vegetarian_can_be_true(self):
        self.recipe.vegetarian = True
        self._assert_recipe_is_valid()

    def test_vegetarian_can_be_false(self):
        self.recipe.vegetarian = False
        self._assert_recipe_is_valid()

    def _assert_recipe_is_valid(self):
        try:
            self.recipe.full_clean()
        except ValidationError:
            self.fail("Test recipe should be valid")

    def _assert_recipe_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.recipe.full_clean()

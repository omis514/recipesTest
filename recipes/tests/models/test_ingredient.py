from django.core.exceptions import ValidationError
from django.test import TestCase
from recipes.models import Recipe, User, Ingredient


class IngredientModelTestCase(TestCase):
    """Unit tests for the Ingredient model."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.author = User.objects.get(username="@johndoe")
        self.recipe = Recipe.objects.create(
            author=self.author,
            title="Test Recipe",
        )
        self.ingredient = Ingredient.objects.create(
            recipe=self.recipe, name="Rice", quantity=1, unit="cup"
        )

    def test_valid_ingredient(self):
        self.__assert_ingredient_is_valid()

    def test_recipe_cannot_be_null(self):
        self.ingredient.recipe = None
        self.__assert_ingredient_is_invalid()

    def test_ingredient_deleted_when_recipe_deleted(self):
        before_count = Ingredient.objects.count()
        self.recipe.delete()
        after_count = Ingredient.objects.count()
        self.assertEqual(after_count, before_count - 1)

    def test_name_cannot_be_blank(self):
        self.ingredient.name = ""
        self.__assert_ingredient_is_invalid()

    def test_name_can_be_100_chars(self):
        self.ingredient.name = "x" * 100
        self.__assert_ingredient_is_valid()

    def test_name_cannot_be_over_100_chars(self):
        self.ingredient.name = "x" * 101
        self.__assert_ingredient_is_invalid()

    def test_quantity_can_be_blank_and_null(self):
        self.ingredient.quantity = None
        self.__assert_ingredient_is_valid()

    def test_quantity_can_be_zero(self):
        self.ingredient.quantity = 0
        self.__assert_ingredient_is_valid()

    def test_unit_can_be_blank(self):
        self.ingredient.unit = ""
        self.__assert_ingredient_is_valid()

    def test_unit_can_be_50_chars(self):
        self.ingredient.unit = "x" * 50
        self.__assert_ingredient_is_valid()

    def test_unit_cannot_be_over_50_chars(self):
        self.ingredient.unit = "x" * 51
        self.__assert_ingredient_is_invalid()

    def test_ingredients_must_be_unique_in_same_recipe(self):
        with self.assertRaises(ValidationError):
            Ingredient(
                recipe=self.recipe, name="Rice", quantity=2, unit="handfuls"
            ).full_clean()

    def test_ingredient_name_can_be_same_in_different_recipes(self):
        recipe_two = Recipe.objects.create(author=self.author, title="Recipe 2")
        try:
            Ingredient(
                recipe=recipe_two, name="Rice", quantity=1, unit="cup"
            ).full_clean()
        except ValidationError:
            self.fail("Should be fine to use same ingredient name in different recipes")

    def test_str_method_full(self):
        self.assertEqual(str(self.ingredient), "1 cup Rice")

    def test_str_method_quantity_name(self):
        self.ingredient.unit = ""
        self.ingredient.save()
        self.assertEqual(str(self.ingredient), "1 Rice")

    def test_str_method_unit_name(self):
        self.ingredient.quantity = None
        self.ingredient.save()
        self.assertEqual(str(self.ingredient), "cup Rice")

    def test_str_method_zero_quantity(self):
        self.ingredient.quantity = 0
        self.ingredient.save()
        self.assertEqual(str(self.ingredient), "0 cup Rice")

    def test_str_method_name(self):
        self.ingredient.unit = ""
        self.ingredient.quantity = None
        self.ingredient.save()
        self.assertEqual(str(self.ingredient), "Rice")

    def __assert_ingredient_is_valid(self):
        try:
            self.ingredient.full_clean()
        except ValidationError:
            self.fail("Test ingredient should be valid")

    def __assert_ingredient_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.ingredient.full_clean()

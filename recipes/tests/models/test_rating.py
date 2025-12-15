"""Unit tests for the Rating model."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from recipes.models import Rating, Recipe, User


class RatingModelTestCase(TestCase):
    """Unit tests for the Rating model."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.recipe = Recipe.objects.create(
            author=self.user,
            title="Test Recipe",
            description="Test Description",
            difficulty=Recipe.Difficulty.EASY,
            time=30,
        )
        self.rating = Rating.objects.create(
            user=self.user,
            recipe=self.recipe,
            rating=5,
        )

    def test_valid_rating(self):
        self._assert_rating_is_valid()

    def test_rating_value_cannot_be_null(self):
        self.rating.rating = None
        self._assert_rating_is_invalid()

    def test_rating_value_cannot_be_zero(self):
        self.rating.rating = 0
        self._assert_rating_is_invalid()

    def test_rating_value_cannot_be_negative(self):
        self.rating.rating = -1
        self._assert_rating_is_invalid()

    def test_rating_value_cannot_be_greater_than_five(self):
        self.rating.rating = 6
        self._assert_rating_is_invalid()

    def test_rating_value_can_be_one(self):
        self.rating.rating = 1
        self._assert_rating_is_valid()

    def test_rating_value_can_be_three(self):
        self.rating.rating = 3
        self._assert_rating_is_valid()

    def test_rating_value_can_be_five(self):
        self.rating.rating = 5
        self._assert_rating_is_valid()

    def test_recipe_cannot_be_null(self):
        self.rating.recipe = None
        self._assert_rating_is_invalid()

    def test_user_cannot_be_null(self):
        self.rating.user = None
        self._assert_rating_is_invalid()

    def test_rating_deleted_when_recipe_deleted(self):
        before_count = Rating.objects.count()
        self.recipe.delete()
        after_count = Rating.objects.count()
        self.assertEqual(after_count, before_count - 1)

    def test_rating_deleted_when_user_deleted(self):
        before_count = Rating.objects.count()
        self.user.delete()
        after_count = Rating.objects.count()
        self.assertEqual(after_count, before_count - 1)

    def test_user_can_rate_multiple_different_recipes(self):
        recipe2 = Recipe.objects.create(
            author=self.user,
            title="Test Recipe 2",
        )
        try:
            Rating.objects.create(user=self.user, recipe=recipe2, rating=4)
        except Exception:
            self.fail("User should be able to rate multiple different recipes")

    def test_recipe_can_have_multiple_ratings_from_different_users(self):
        user2 = User.objects.create_user(
            username="@janedoe",
            email="jane@example.com",
            password="Password123",
            first_name="Jane",
            last_name="Doe",
        )
        try:
            Rating.objects.create(user=user2, recipe=self.recipe, rating=4)
        except Exception:
            self.fail(
                "Recipe should be able to have multiple ratings from different users"
            )

    def test_rating_must_be_unique_per_user_and_recipe(self):
        duplicate_rating = Rating(user=self.user, recipe=self.recipe, rating=3)
        with self.assertRaises(ValidationError):
            duplicate_rating.full_clean()

        with self.assertRaises(IntegrityError):
            duplicate_rating.save()

    def test_str_method(self):
        self.assertEqual(
            str(self.rating),
            f"5 Star rating by {self.user.username} for {self.recipe.title}",
        )

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.rating.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.rating.updated_at)

    def _assert_rating_is_valid(self):
        try:
            self.rating.full_clean()
        except ValidationError:
            self.fail("Test rating should be valid")

    def _assert_rating_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.rating.full_clean()

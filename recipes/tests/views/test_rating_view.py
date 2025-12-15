"""Tests for the rating views (submit_rating and delete_rating)."""

import json
from django.test import TestCase
from django.urls import reverse
from recipes.models import Recipe, User, Rating
from recipes.tests.helpers import LogInTester


class SubmitRatingViewTestCase(TestCase, LogInTester):
    """Tests for the submit_rating view."""

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
        )
        self.url = reverse("submit_rating", kwargs={"recipe_pk": self.recipe.pk})

    def test_submit_rating_url(self):
        """Test that the URL is correct."""
        self.assertEqual(self.url, f"/recipes/{self.recipe.pk}/rate/")

    def test_submit_rating_requires_login(self):
        """Test that submit_rating requires login."""
        response = self.client.post(self.url, {"rating": "5"})
        self.assertRedirects(response, f"/log_in/?next={self.url}")

    def test_submit_rating_requires_post(self):
        """Test that submit_rating only accepts POST requests."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)  # Method not allowed

    def test_submit_rating_success(self):
        """Test successfully submitting a rating."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url, {"rating": "5"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Rating saved successfully.")
        self.assertEqual(data["user_rating"], 5)

        # Verify rating was created
        rating = Rating.objects.get(recipe=self.recipe, user=self.user)
        self.assertEqual(rating.rating, 5)

    def test_submit_rating_updates_existing_rating(self):
        """Test that submitting a new rating updates the existing one."""
        # Create initial rating
        Rating.objects.create(recipe=self.recipe, user=self.user, rating=3)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url, {"rating": "5"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verify rating was updated (not duplicated)
        ratings = Rating.objects.filter(recipe=self.recipe, user=self.user)
        self.assertEqual(ratings.count(), 1)
        self.assertEqual(ratings.first().rating, 5)

    def test_submit_rating_calculates_average(self):
        """Test that average rating is calculated correctly."""
        # Add another user's rating
        Rating.objects.create(recipe=self.recipe, user=self.other_user, rating=3)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url, {"rating": "5"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["average_rating"], 4.0)  # (3 + 5) / 2
        self.assertEqual(data["rating_count"], 2)

    def test_submit_rating_invalid_rating_too_low(self):
        """Test that rating below 1 is rejected."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url, {"rating": "0"})

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("error", data)

    def test_submit_rating_invalid_rating_too_high(self):
        """Test that rating above 5 is rejected."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url, {"rating": "6"})

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("error", data)

    def test_submit_rating_invalid_rating_not_integer(self):
        """Test that non-integer rating is rejected."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url, {"rating": "3.5"})

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("error", data)

    def test_submit_rating_missing_rating(self):
        """Test that missing rating parameter is rejected."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("error", data)

    def test_submit_rating_invalid_recipe(self):
        """Test that invalid recipe ID returns 404."""
        self.client.login(username=self.user.username, password="Password123")
        invalid_url = reverse("submit_rating", kwargs={"recipe_pk": 9999})
        response = self.client.post(invalid_url, {"rating": "5"})

        self.assertEqual(response.status_code, 404)

    def test_submit_rating_all_valid_ratings(self):
        """Test that all valid ratings (1-5) are accepted."""
        self.client.login(username=self.user.username, password="Password123")

        for rating_value in range(1, 6):
            response = self.client.post(self.url, {"rating": str(rating_value)})
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data["success"])
            self.assertEqual(data["user_rating"], rating_value)

    def test_submit_rating_multiple_users(self):
        """Test that multiple users can rate the same recipe."""
        self.client.login(username=self.user.username, password="Password123")
        response1 = self.client.post(self.url, {"rating": "5"})
        self.assertEqual(response1.status_code, 200)

        self.client.login(username=self.other_user.username, password="Password123")
        response2 = self.client.post(self.url, {"rating": "3"})
        self.assertEqual(response2.status_code, 200)

        # Verify both ratings exist
        ratings = Rating.objects.filter(recipe=self.recipe)
        self.assertEqual(ratings.count(), 2)
        self.assertEqual(ratings.get(user=self.user).rating, 5)
        self.assertEqual(ratings.get(user=self.other_user).rating, 3)


class DeleteRatingViewTestCase(TestCase, LogInTester):
    """Tests for the delete_rating view."""

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
        )
        self.url = reverse("delete_rating", kwargs={"recipe_pk": self.recipe.pk})

    def test_delete_rating_url(self):
        """Test that the URL is correct."""
        self.assertEqual(self.url, f"/recipes/{self.recipe.pk}/rate/delete/")

    def test_delete_rating_requires_login(self):
        """Test that delete_rating requires login."""
        response = self.client.post(self.url)
        self.assertRedirects(response, f"/log_in/?next={self.url}")

    def test_delete_rating_requires_post(self):
        """Test that delete_rating only accepts POST requests."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)  # Method not allowed

    def test_delete_rating_success(self):
        """Test successfully deleting a rating."""
        # Create rating first
        Rating.objects.create(recipe=self.recipe, user=self.user, rating=5)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Rating removed successfully.")

        # Verify rating was deleted
        self.assertFalse(
            Rating.objects.filter(recipe=self.recipe, user=self.user).exists()
        )

    def test_delete_rating_no_rating_exists(self):
        """Test deleting a rating when none exists (should still succeed)."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

    def test_delete_rating_calculates_average_after_deletion(self):
        """Test that average rating is recalculated after deletion."""
        # Create multiple ratings
        Rating.objects.create(recipe=self.recipe, user=self.user, rating=5)
        Rating.objects.create(recipe=self.recipe, user=self.other_user, rating=3)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        # After deleting user's rating, only other_user's rating remains
        self.assertEqual(data["average_rating"], 3.0)
        self.assertEqual(data["rating_count"], 1)

    def test_delete_rating_all_ratings_deleted(self):
        """Test that average is 0 when all ratings are deleted."""
        # Create rating
        Rating.objects.create(recipe=self.recipe, user=self.user, rating=5)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        # No ratings left
        self.assertEqual(data["average_rating"], 0.0)
        self.assertEqual(data["rating_count"], 0)

    def test_delete_rating_only_deletes_own_rating(self):
        """Test that users can only delete their own ratings."""
        # Create ratings for both users
        Rating.objects.create(recipe=self.recipe, user=self.user, rating=5)
        Rating.objects.create(recipe=self.recipe, user=self.other_user, rating=3)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        # Verify only user's rating was deleted
        self.assertFalse(
            Rating.objects.filter(recipe=self.recipe, user=self.user).exists()
        )
        self.assertTrue(
            Rating.objects.filter(recipe=self.recipe, user=self.other_user).exists()
        )

    def test_delete_rating_invalid_recipe(self):
        """Test that invalid recipe ID returns 404."""
        self.client.login(username=self.user.username, password="Password123")
        invalid_url = reverse("delete_rating", kwargs={"recipe_pk": 9999})
        response = self.client.post(invalid_url)

        self.assertEqual(response.status_code, 404)

    def test_delete_rating_multiple_users(self):
        """Test that each user can delete their own rating independently."""
        # Create ratings for both users
        Rating.objects.create(recipe=self.recipe, user=self.user, rating=5)
        Rating.objects.create(recipe=self.recipe, user=self.other_user, rating=3)

        # User deletes their rating
        self.client.login(username=self.user.username, password="Password123")
        response1 = self.client.post(self.url)
        self.assertEqual(response1.status_code, 200)

        # Other user deletes their rating
        self.client.login(username=self.other_user.username, password="Password123")
        response2 = self.client.post(self.url)
        self.assertEqual(response2.status_code, 200)

        # Verify both ratings are deleted
        self.assertFalse(Rating.objects.filter(recipe=self.recipe).exists())

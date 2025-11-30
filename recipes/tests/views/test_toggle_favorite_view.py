"""Tests of the toggle favorite view."""

from django.test import TestCase
from django.urls import reverse
from recipes.models import Recipe, User
from recipes.tests.helpers import LogInTester, reverse_with_next


class ToggleFavoriteViewTestCase(TestCase, LogInTester):
    """Tests of the toggle favorite view."""

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
        self.url = reverse("toggle_favorite", kwargs={"pk": self.recipe.pk})

    def test_toggle_favorite_url(self):
        self.assertEqual(self.url, f"/recipes/{self.recipe.pk}/favorite/")

    def test_get_toggle_favorite_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertFalse(self._is_logged_in())

    def test_post_toggle_favorite_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertFalse(self._is_logged_in())

    def test_favorite_recipe(self):
        self.client.login(username=self.user.username, password="Password123")
        self.assertEqual(self.recipe.favorites.count(), 0)

        response = self.client.post(self.url, follow=True)

        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.favorites.count(), 1)
        self.assertTrue(self.user in self.recipe.favorites.all())

        detail_url = reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        self.assertRedirects(
            response, detail_url, status_code=302, target_status_code=200
        )

    def test_unfavorite_recipe(self):
        self.client.login(username=self.user.username, password="Password123")
        self.recipe.favorites.add(self.user)
        self.assertEqual(self.recipe.favorites.count(), 1)

        response = self.client.post(self.url, follow=True)

        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.favorites.count(), 0)
        self.assertFalse(self.user in self.recipe.favorites.all())

        detail_url = reverse("recipe_detail", kwargs={"pk": self.recipe.pk})
        self.assertRedirects(
            response, detail_url, status_code=302, target_status_code=200
        )

    def test_toggle_favorite_with_invalid_id(self):
        self.client.login(username=self.user.username, password="Password123")
        invalid_url = reverse("toggle_favorite", kwargs={"pk": 9999})
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)

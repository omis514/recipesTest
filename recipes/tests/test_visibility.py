from django.test import TestCase
from django.urls import reverse

from recipes.models import User, Recipe


class RecipeVisibilityTest(TestCase):
    """Tests of the visibility for recipes."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="Password123",
            first_name="User",
            last_name="One",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="Password123",
            first_name="User",
            last_name="Two",
        )

        # Public Recipe by User 1
        self.public_recipe = Recipe.objects.create(
            author=self.user1,
            title="Public Recipe",
            description="This is public",
            difficulty=1,
            spiciness=1,
            cuisine=1,
            time=30,
            visibility=Recipe.Visibility.PUBLIC,
        )

        # Private Recipe by User 1
        self.private_recipe = Recipe.objects.create(
            author=self.user1,
            title="Private Recipe",
            description="This is private",
            difficulty=1,
            spiciness=1,
            cuisine=1,
            time=30,
            visibility=Recipe.Visibility.PRIVATE,
        )

        # Public Recipe by User 2
        self.public_recipe_2 = Recipe.objects.create(
            author=self.user2,
            title="Public Recipe 2",
            description="This is public too",
            difficulty=1,
            spiciness=1,
            cuisine=1,
            time=30,
            visibility=Recipe.Visibility.PUBLIC,
        )

    def test_dashboard_feed_visibility(self):
        """Test that dashboard feed follows visibility rules."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        # Should see own private, own public, and others public
        self.assertContains(response, self.public_recipe.title)
        self.assertContains(response, self.private_recipe.title)
        self.assertContains(response, self.public_recipe_2.title)

        # Switch to user 2
        self.client.force_login(self.user2)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        # Should see own public, others public, but NOT others private
        self.assertContains(response, self.public_recipe.title)
        self.assertContains(response, self.public_recipe_2.title)
        self.assertNotContains(response, self.private_recipe.title)

    def test_home_page_feed_anonymous(self):
        """Test that public recipes appear on home page for anonymous users."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_recipe.title)
        self.assertContains(response, self.public_recipe_2.title)
        self.assertNotContains(response, self.private_recipe.title)

    def test_browse_recipes_authenticated_own(self):
        """Test that authenticated user sees their own private recipes."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("recipe_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_recipe.title)
        self.assertContains(response, self.private_recipe.title)
        self.assertContains(response, self.public_recipe_2.title)

    def test_browse_recipes_authenticated_other(self):
        """Test that authenticated user does not see others private recipes."""
        self.client.force_login(self.user2)
        response = self.client.get(reverse("recipe_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_recipe.title)
        self.assertContains(response, self.public_recipe_2.title)
        self.assertNotContains(response, self.private_recipe.title)

    def test_recipe_detail_public_anonymous(self):
        """Test anonymous access to public recipe."""
        url = reverse("recipe_detail", kwargs={"pk": self.public_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_recipe.title)

    def test_recipe_detail_private_anonymous(self):
        """Test anonymous access to private recipe."""
        url = reverse("recipe_detail", kwargs={"pk": self.private_recipe.pk})
        response = self.client.get(url)
        # Should be 403 PermissionDenied
        self.assertEqual(response.status_code, 403)

    def test_recipe_detail_private_author(self):
        """Test author access to private recipe."""
        self.client.force_login(self.user1)
        url = reverse("recipe_detail", kwargs={"pk": self.private_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.private_recipe.title)

    def test_recipe_detail_private_other(self):
        """Test other user access to private recipe."""
        self.client.force_login(self.user2)
        url = reverse("recipe_detail", kwargs={"pk": self.private_recipe.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_observe_profile_recipes(self):
        """Test valid recipes shown on profile page."""
        # User 2 viewing User 1 profile
        self.client.force_login(self.user2)
        url = reverse("observe_profile", kwargs={"username": self.user1.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_recipe.title)
        self.assertNotContains(response, self.private_recipe.title)

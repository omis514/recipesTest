from django.test import TestCase
from django.urls import reverse
from recipes.models import User, Recipe, Report

from recipes.tests.helpers import LogInTester


class ReportedRecipesViewTestCase(TestCase, LogInTester):
    """Tests for the reported recipes views (staff only)."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.staff_user = User.objects.create_user(
            username="@admin",
            first_name="Admin",
            last_name="User",
            email="admin@example.org",
            password="Password123",
            is_staff=True,
        )
        self.recipe = Recipe.objects.create(
            author=self.user,
            title="Test Recipe",
            description="A delicious test recipe.",
            time=30,
            difficulty=1,
            spiciness=1,
            cuisine=1,
        )
        self.report = Report.objects.create(
            recipe=self.recipe,
            reporter=self.user,
            summary="Inappropriate content.",
        )
        self.list_url = reverse("reported_recipes_list")
        self.detail_url = reverse(
            "recipe_reports_detail", kwargs={"recipe_id": self.recipe.id}
        )

    def test_reported_recipes_list_redirects_anonymous(self):
        """Test that anonymous users are redirected to login."""
        response = self.client.get(self.list_url)
        self.assertRedirects(response, f"/log_in/?next={self.list_url}")

    def test_reported_recipes_list_redirects_non_staff(self):
        """Test that non-staff users are redirected (access denied)."""
        self.client.login(username="@johndoe", password="Password123")
        response = self.client.get(self.list_url)
        # user_passes_test redirects to login_url if test fails
        self.assertRedirects(
            response, f"/log_in/?next={self.list_url}", fetch_redirect_response=False
        )

    def test_reported_recipes_list_accessible_by_staff(self):
        """Test that staff users can access the list."""
        self.client.login(username="@admin", password="Password123")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reported_recipes.html")
        self.assertIn("page_obj", response.context)
        self.assertEqual(len(response.context["page_obj"]), 1)
        self.assertEqual(response.context["page_obj"][0], self.recipe)

    def test_recipe_reports_detail_redirects_anonymous(self):
        """Test that anonymous users are redirected to login."""
        response = self.client.get(self.detail_url)
        self.assertRedirects(response, f"/log_in/?next={self.detail_url}")

    def test_recipe_reports_detail_redirects_non_staff(self):
        """Test that non-staff users are redirected (access denied)."""
        self.client.login(username="@johndoe", password="Password123")
        response = self.client.get(self.detail_url)
        self.assertRedirects(
            response, f"/log_in/?next={self.detail_url}", fetch_redirect_response=False
        )

    def test_recipe_reports_detail_accessible_by_staff(self):
        """Test that staff users can access the detail view."""
        self.client.login(username="@admin", password="Password123")
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recipe_reports_detail.html")
        self.assertEqual(response.context["recipe"], self.recipe)
        self.assertIn("page_obj", response.context)
        self.assertEqual(len(response.context["page_obj"]), 1)
        self.assertEqual(response.context["page_obj"][0], self.report)

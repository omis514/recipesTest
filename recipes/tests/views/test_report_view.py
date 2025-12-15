from django.test import TestCase
from django.urls import reverse
from recipes.models import User, Recipe, Report
from recipes.forms import ReportForm

from recipes.tests.helpers import LogInTester


class ReportRecipeViewTestCase(TestCase, LogInTester):
    """Tests for the report recipe view."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.recipe = Recipe.objects.create(
            author=self.user,
            title="Test Recipe",
            description="A delicious test recipe.",
            time=30,
            difficulty=1,
            spiciness=1,
            cuisine=1,
        )
        self.url = reverse("report_recipe", kwargs={"pk": self.recipe.id})

    def test_report_recipe_redirects_anonymous(self):
        """Test that anonymous users are redirected to login."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/log_in/?next={self.url}")

    def test_report_recipe_accessible_by_authenticated_user(self):
        """Test that authenticated users can access the report form."""
        self.client.login(username="@johndoe", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "report_recipe.html")
        self.assertIsInstance(response.context["form"], ReportForm)

    def test_report_recipe_submission(self):
        """Test submitting a valid report."""
        self.client.login(username="@johndoe", password="Password123")
        form_data = {"summary": "Inappropriate content."}
        response = self.client.post(self.url, form_data)
        self.assertRedirects(
            response, reverse("recipe_detail", kwargs={"pk": self.recipe.id})
        )

        # Check that report was created
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.first()
        self.assertEqual(report.recipe, self.recipe)
        self.assertEqual(report.reporter, self.user)
        self.assertEqual(report.summary, "Inappropriate content.")

    def test_report_recipe_invalid_submission(self):
        """Test submitting an invalid report (empty summary)."""
        self.client.login(username="@johndoe", password="Password123")
        form_data = {"summary": ""}
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "report_recipe.html")
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Report.objects.count(), 0)

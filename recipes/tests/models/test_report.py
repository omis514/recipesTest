from django.core.exceptions import ValidationError
from django.test import TestCase
from recipes.models import Recipe, User, Report


class ReportModelTestCase(TestCase):
    """Unit tests for the Report model."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.reporter = User.objects.create_user(
            username="@janedoe",
            first_name="Jane",
            last_name="Doe",
            email="janedoe@example.org",
            password="Password123",
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
            reporter=self.reporter,
            summary="Inappropriate content.",
        )

    def test_valid_report(self):
        """Test that a valid report can be created."""
        self._assert_report_is_valid()

    def test_report_must_have_recipe(self):
        """Test that a report must be associated with a recipe."""
        self.report.recipe = None
        self._assert_report_is_invalid()

    def test_report_must_have_reporter(self):
        """Test that a report must be associated with a reporter."""
        self.report.reporter = None
        self._assert_report_is_invalid()

    def test_report_summary_cannot_be_blank(self):
        """Test that a report summary cannot be blank."""
        self.report.summary = ""
        self._assert_report_is_invalid()

    def test_report_summary_can_be_1000_characters(self):
        """Test that a report summary can be up to 1000 characters."""
        self.report.summary = "x" * 1000
        self._assert_report_is_valid()

    def test_report_summary_cannot_be_over_1000_characters(self):
        """Test that a report summary cannot exceed 1000 characters."""
        self.report.summary = "x" * 1001
        self._assert_report_is_invalid()

    def test_string_representation(self):
        """Test the string representation of the report."""
        self.assertEqual(
            str(self.report),
            f"Report by {self.reporter.username} on {self.recipe.title}",
        )

    def _assert_report_is_valid(self):
        try:
            self.report.full_clean()
        except ValidationError:
            self.fail("Test report should be valid")

    def _assert_report_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.report.full_clean()

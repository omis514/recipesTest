"""Unit tests of the report form."""

from django import forms
from django.test import TestCase
from recipes.forms import ReportForm
from recipes.models import Report, Recipe, User


class ReportFormTestCase(TestCase):
    """Unit tests of the report form."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.recipe = Recipe.objects.create(
            author=self.user,
            title="Test Recipe",
            description="A test recipe description",
            difficulty=Recipe.Difficulty.EASY,
            time=45,
        )
        self.form_input = {
            "summary": "This is a test report summary.",
        }

    def test_form_has_necessary_fields(self):
        form = ReportForm()
        self.assertIn("summary", form.fields)
        self.assertEqual(len(form.fields), 1)

    def test_form_summary_field_is_char_field(self):
        form = ReportForm()
        self.assertTrue(isinstance(form.fields["summary"], forms.CharField))
        self.assertTrue(isinstance(form.fields["summary"].widget, forms.Textarea))

    def test_valid_report_form(self):
        form = ReportForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_summary_is_required(self):
        self.form_input["summary"] = ""
        form = ReportForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn("summary", form.errors)

    def test_form_summary_can_be_1000_chars(self):
        self.form_input["summary"] = "x" * 1000
        form = ReportForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_summary_cannot_be_over_1000_chars(self):
        self.form_input["summary"] = "x" * 1001
        form = ReportForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn("summary", form.errors)

    def test_form_must_save_correctly(self):
        form = ReportForm(data=self.form_input)
        self.assertTrue(form.is_valid())
        report = form.save(commit=False)
        report.recipe = self.recipe
        report.reporter = self.user
        report.save()
        self.assertEqual(report.summary, "This is a test report summary.")
        self.assertEqual(report.recipe, self.recipe)
        self.assertEqual(report.reporter, self.user)

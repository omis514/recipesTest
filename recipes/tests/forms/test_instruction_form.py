"""Unit tests of the instruction form."""

from django import forms
from django.test import TestCase
from recipes.forms import InstructionForm
from recipes.models import Instruction, Recipe, User


class InstructionFormTestCase(TestCase):
    """Unit tests of the instruction form."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.author = User.objects.get(username="@johndoe")
        self.recipe = Recipe.objects.create(
            author=self.author,
            title="Test Recipe",
        )
        self.form_input = {
            "step": 1,
            "description": "First, prepare the ingredients.",
        }

    def test_form_has_necessary_fields(self):
        form = InstructionForm()
        self.assertIn("step", form.fields)
        self.assertIn("description", form.fields)

    def test_form_step_field_is_integer_field(self):
        form = InstructionForm()
        self.assertTrue(isinstance(form.fields["step"], forms.IntegerField))

    def test_form_step_field_widget_is_number_input(self):
        form = InstructionForm()
        self.assertTrue(isinstance(form.fields["step"].widget, forms.NumberInput))

    def test_form_description_field_is_char_field(self):
        form = InstructionForm()
        self.assertTrue(isinstance(form.fields["description"], forms.CharField))

    def test_form_description_field_widget_is_textarea(self):
        form = InstructionForm()
        self.assertTrue(isinstance(form.fields["description"].widget, forms.Textarea))

    def test_valid_instruction_form(self):
        form = InstructionForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_step_is_required(self):
        self.form_input["step"] = ""
        form = InstructionForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn("step", form.errors)

    def test_form_step_can_be_positive_integer(self):
        self.form_input["step"] = 5
        form = InstructionForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_step_can_be_one(self):
        self.form_input["step"] = 1
        form = InstructionForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_description_is_required(self):
        self.form_input["description"] = ""
        form = InstructionForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)

    def test_form_description_can_be_500_chars(self):
        self.form_input["description"] = "x" * 500
        form = InstructionForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_description_cannot_be_over_500_chars(self):
        self.form_input["description"] = "x" * 501
        form = InstructionForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)

    def test_form_must_save_correctly(self):
        form = InstructionForm(data=self.form_input)
        self.assertTrue(form.is_valid())
        instruction = form.save(commit=False)
        instruction.recipe = self.recipe
        instruction.save()
        self.assertEqual(instruction.step, 1)
        self.assertEqual(instruction.description, "First, prepare the ingredients.")

    def test_form_uses_model_validation(self):
        # Description that's too long
        self.form_input["description"] = "x" * 501
        form = InstructionForm(data=self.form_input)
        self.assertFalse(form.is_valid())

from django import forms
from recipes.models import Ingredient


class IngredientForm(forms.ModelForm):
    """Form for a single ingredient."""

    UNIT_CHOICES = [
        ("", "Select unit"),
        ("tsp", "tsp"),
        ("tbsp", "tbsp"),
        ("cup", "cup"),
        ("cups", "cups"),
        ("ml", "ml"),
        ("l", "l"),
        ("g", "g"),
        ("kg", "kg"),
        ("oz", "oz"),
        ("lb", "lb"),
        ("lbs", "lbs"),
        ("piece", "piece"),
        ("pieces", "pieces"),
        ("pinch", "pinch"),
        ("dash", "dash"),
        ("clove", "clove"),
    ]

    unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    class Meta:
        """Form options."""

        model = Ingredient
        fields = ["name", "quantity", "unit"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ingredient name",
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Amount",
                    "min": "0",
                    "step": "0.01",
                }
            ),
        }

    def clean_name(self):
        """Validate that ingredient name is provided."""
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise forms.ValidationError("Ingredient name is required.")
        return name

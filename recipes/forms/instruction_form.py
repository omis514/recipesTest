from django import forms
from recipes.models import Instruction


class InstructionForm(forms.ModelForm):
    """Form for a single instruction step."""

    class Meta:
        """Form options."""

        model = Instruction
        fields = ["step", "description", "image"]
        widgets = {
            "step": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Describe this step...",
                }
            ),
            "image": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }

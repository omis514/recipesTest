from django import forms
from recipes.models import Report


class ReportForm(forms.ModelForm):
    """Form for reporting a recipe."""

    class Meta:
        """Form options."""

        model = Report
        fields = ["summary"]
        widgets = {
            "summary": forms.Textarea(
                attrs={
                    "rows": 5,
                    "class": "form-control",
                    "placeholder": "Please provide details about why you are reporting this recipe...",
                }
            ),
        }
        labels = {
            "summary": "Report Summary",
        }
        help_texts = {
            "summary": "Please provide a clear explanation of why you are reporting this recipe.",
        }

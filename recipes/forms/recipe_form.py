from django import forms
from recipes.models import Recipe


class RecipeForm(forms.ModelForm):
    """Form to create a new recipe."""

    class Meta:
        """Form options."""

        model = Recipe
        fields = ["title", "description", "difficulty", "image", "time"]

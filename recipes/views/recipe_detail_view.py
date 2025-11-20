# recipes/views/recipe_detail_view.py

from django.shortcuts import render, get_object_or_404
from recipes.models import Recipe


def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, "recipe_detail.html", {"recipe": recipe})

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from recipes.models import Recipe


@login_required
def toggle_favorite(request, pk):
    """
    Toggle the favorite status of a recipe for.
    """
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.user in recipe.favorites.all():
        recipe.favorites.remove(request.user)
    else:
        recipe.favorites.add(request.user)

    return redirect('recipe_detail', pk=pk)
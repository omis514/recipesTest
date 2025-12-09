from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Avg
from recipes.models import Recipe


@login_required
def toggle_favorite(request, pk):
    """
    Toggle the favorite status of a recipe for.
    """
    recipe = get_object_or_404(Recipe, pk=pk)
    user = request.user

    if user in recipe.favorites.all():
        recipe.favorites.remove(user)
        user.recipes_favourited_num -= 1
    else:
        user.recipes_favourited_num += 1
        recipe.favorites.add(user)

    # Calculate preferred spiceness based on all favorited recipes
    favorited_recipes = user.favorite_recipes.all()
    if favorited_recipes.exists():
        # Calculate average spiciness of all favorited recipes
        avg_spiciness = favorited_recipes.aggregate(Avg("spiciness"))["spiciness__avg"]
        user.preferred_spiceness = round(avg_spiciness, 2)
    else:
        # If no favorites, reset to default
        user.preferred_spiceness = 1.5

    user.save()

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)

    return redirect("recipe_detail", pk=pk)

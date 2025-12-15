from django.shortcuts import render

from recipes.models import Recipe
from recipes.views.decorators import login_prohibited


@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    feed_recipes = (
        Recipe.objects.filter(visibility=Recipe.Visibility.PUBLIC)
        .select_related("author")
        .order_by("-created_at")[:6]
    )

    return render(request, "home.html", {"feed_recipes": feed_recipes})

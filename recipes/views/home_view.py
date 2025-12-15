from django.shortcuts import render

from recipes.models import Recipe
from recipes.views.decorators import login_prohibited
from django.db.models import Count, Prefetch, Q, Avg
from recipes.models import Recipe, Comment


@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    top_comment_prefetch = Prefetch(
        "comments",
        queryset=Comment.objects.select_related("author")
        .annotate(likes_count=Count("likes"))
        .order_by("-likes_count", "-created_at")[:1],
        to_attr="top_comment_list",
    )

    feed_recipes = (
        Recipe.objects.filter(visibility=Recipe.Visibility.PUBLIC)
        .select_related("author")
        .prefetch_related(top_comment_prefetch, "comments", "ratings", "favorites")
        .annotate(
            total_comments=Count("comments", distinct=True),
            average_rating=Avg("ratings__rating"),
            rating_count=Count("ratings", distinct=True),
        )
        .order_by("-created_at")[:6]
    )

    for recipe in feed_recipes:
        recipe.top_comment = (
            recipe.top_comment_list[0]
            if hasattr(recipe, "top_comment_list") and recipe.top_comment_list
            else None
        )

    return render(request, "home.html", {"feed_recipes": feed_recipes})

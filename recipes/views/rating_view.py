from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from recipes.models import Recipe, Rating
from django.db.models import Avg, Count

@login_required
@require_POST
def submit_rating(request, recipe_pk):
    """Handles rating submission."""

    recipe = get_object_or_404(Recipe, pk=recipe_pk)
    rating_str = request.POST.get("rating")

    try:
        rating = int(rating_str)
        if not 1 <= rating <= 5:
            raise ValueError("Score must be between 1 and 5")
    except(TypeError, ValueError):
        return JsonResponse({"success": False, "error": "Invalid rating."}, status=400)

    Rating.objects.update_or_create(
        recipe=recipe,
        user=request.user,
        defaults={"rating": rating},
    )

    recipe_metrics = Recipe.objects.filter(pk=recipe_pk).aggregate(
        average_rating=Avg("ratings__rating"),
        rating_count=Count("ratings"),
    )

    average_rating = recipe_metrics.get('average_rating') or 0.0
    rating_count = recipe_metrics.get('rating_count') or 0

    return JsonResponse({
        "success": True,
        "message": "Rating saved successfully.",
        "average_rating": f"{average_rating:.2f}",
        "rating_count": rating_count,
        "user_rating": rating
    })

@login_required
@require_POST
def delete_rating(request, recipe_pk):
    """Handles rating deletion."""
    recipe = get_object_or_404(Recipe, pk=recipe_pk)

    Rating.objects.filter(recipe=recipe, user=request.user).delete()

    recipe_metrics = Recipe.objects.filter(pk=recipe_pk).aggregate(
        average_rating=Avg("ratings__rating"),
        rating_count=Count("ratings"),
    )

    average_rating = recipe_metrics.get('average_rating') or 0.0
    rating_count = recipe_metrics.get('rating_count') or 0

    return JsonResponse({
        "success": True,
        "message": "Rating removed successfully.",
        "average_rating": f"{average_rating:.2f}",
        "rating_count": rating_count,
    })

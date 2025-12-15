from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from recipes.models import User, Follow, Recipe
from django.shortcuts import render


@login_required
def observeProfile(request, username):

    if username == request.user.username:
        return redirect("user_profile")

    target_user = get_object_or_404(User, username=username)

    # Same pattern as search_users
    following_ids = set(
        Follow.objects.filter(follower=request.user).values_list(
            "following_id", flat=True
        )
    )

    # Add is_followed attribute so follow_button.html works
    target_user.is_followed = target_user.id in following_ids

    # Annotate recipes with total_comments, average_rating, and rating_count
    # to match what the template expects (same as recipe_list_view)
    user_recipes = (
        target_user.recipes.filter(visibility=Recipe.Visibility.PUBLIC)
        .select_related("author")
        .prefetch_related("comments", "ratings")
        .annotate(
            total_comments=Count("comments", distinct=True),
            average_rating=Avg("ratings__rating"),
            rating_count=Count("ratings", distinct=True),
        )
    )

    context = {
        "target_user": target_user,
        "user_recipes": user_recipes,
    }

    return render(request, "observe_user.html", context)

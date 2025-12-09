from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Prefetch, F
from django.db.models.functions import Abs
from recipes.models import Recipe, Comment


@login_required
def dashboard(request):
    """
    Display the current user's dashboard.

    This view renders the dashboard page for the authenticated user.
    It ensures that only logged-in users can access the page. If a user
    is not authenticated, they are automatically redirected to the login
    page.
    """

    current_user = request.user

    # Prefetch top comment for each recipe (most liked comment)
    top_comment_prefetch = Prefetch(
        "comments",
        queryset=Comment.objects.select_related("author")
        .annotate(likes_count=Count("likes"))
        .order_by("-likes_count", "-created_at")[:1],
        to_attr="top_comment_list",
    )

    # Get user's preferred spiceness
    preferred_spiceness = current_user.preferred_spiceness

    # Get recipes sorted by proximity to user's preferred spiceness
    # Calculate absolute difference between recipe spiciness and preferred spiceness
    feed_recipes = (
        Recipe.objects.select_related("author")
        .prefetch_related(
            top_comment_prefetch, "comments"  # Also get all comments for counting
        )
        .annotate(
            total_comments=Count("comments", distinct=True),
            spiciness_diff=Abs(F("spiciness") - preferred_spiceness),
        )
        # Sort by spiciness proximity, then by newest
        .order_by("spiciness_diff", "-created_at")[:6]
    )

    # Process recipes to add top comment
    for recipe in feed_recipes:
        recipe.top_comment = (
            recipe.top_comment_list[0]
            if hasattr(recipe, "top_comment_list") and recipe.top_comment_list
            else None
        )

    return render(
        request,
        "dashboard.html",
        {
            "user": current_user,
            "feed_recipes": feed_recipes,
        },
    )

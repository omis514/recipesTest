from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch, F, Q, Avg
from django.db.models.functions import Abs
from django.shortcuts import render

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

    preferred_spiceness = current_user.preferred_spiceness

    feed_recipes = (
        Recipe.objects.select_related("author")
        .prefetch_related(
            top_comment_prefetch,
            "comments",  # for counting comments
            "ratings",  # for consistency / potential template usage
            "favorites",  # if template checks favorites/all
        )
        .annotate(
            total_comments=Count("comments", distinct=True),
            spiciness_diff=Abs(F("spiciness") - preferred_spiceness),
            # --- ADD THESE TWO to match recipe_list ---
            average_rating=Avg("ratings__rating"),
            rating_count=Count("ratings", distinct=True),
        )
        .filter(Q(visibility=Recipe.Visibility.PUBLIC) | Q(author=current_user))
        .order_by("spiciness_diff", "-created_at")[:6]
    )

    # Add top_comment + is_favorited (to match recipe_list behaviour)
    for recipe in feed_recipes:
        recipe.top_comment = (
            recipe.top_comment_list[0]
            if getattr(recipe, "top_comment_list", None)
            else None
        )
        recipe.is_favorited = current_user in recipe.favorites.all()

    return render(
        request,
        "dashboard.html",
        {
            "user": current_user,
            "feed_recipes": feed_recipes,
        },
    )

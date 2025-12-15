# recipes/views/recipe_detail_view.py

from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q, Avg
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from recipes.models import Recipe, Comment, Rating


def recipe_list(request):
    """Display all recipes in a TikTok-style grid layout with top comments."""

    # Prefetch top comment for each recipe (most liked comment)
    top_comment_prefetch = Prefetch(
        "comments",
        queryset=Comment.objects.select_related("author")
        .annotate(likes_count=Count("likes"))
        .order_by("-likes_count", "-created_at")[:1],
        to_attr="top_comment_list",
    )

    # Get all recipes with related data
    recipes = (
        Recipe.objects.select_related("author")
        .prefetch_related(
            top_comment_prefetch, "comments"  # Also get all comments for counting
        )
        .annotate(total_comments=Count("comments", distinct=True))
    )

    # Filter by difficulty if requested
    difficulty = request.GET.get("difficulty")
    if difficulty:
        recipes = recipes.filter(difficulty=difficulty)

    # Filter by search term if provided
    search = request.GET.get("search", "").strip()
    if search:
        recipes = recipes.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    # Sorting options
    sort_by = request.GET.get("sort", "newest")
    if sort_by == "popular":
        recipes = recipes.order_by("-total_comments", "-created_at")
    elif sort_by == "oldest":
        recipes = recipes.order_by("created_at")
    else:  # newest (default)
        recipes = recipes.order_by("-created_at")

    # Pagination - 12 recipes per page
    paginator = Paginator(recipes, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Process recipes to add top comment
    for recipe in page_obj.object_list:
        recipe.top_comment = (
            recipe.top_comment_list[0]
            if hasattr(recipe, "top_comment_list") and recipe.top_comment_list
            else None
        )

    context = {
        "page_obj": page_obj,
        "recipes": page_obj.object_list,
        "difficulties": Recipe.Difficulty.choices,
        "selected_difficulty": difficulty,
        "search_term": search,
        "sort_by": sort_by,
    }
    return render(request, "recipe_list.html", context)


def recipe_detail_view(request, pk):
    from recipes.models import Instruction, Follow

    recipe = get_object_or_404(
        Recipe.objects.prefetch_related(
            "ingredients",
            Prefetch("instructions", queryset=Instruction.objects.order_by("step")),
            "ratings",
        ).select_related("author"),
        pk=pk,
    )

    if recipe.visibility == Recipe.Visibility.PRIVATE:
        if not request.user.is_authenticated or request.user != recipe.author:
            raise PermissionDenied("You do not have permission to view this recipe.")

    ratings_list = recipe.ratings.all()
    if ratings_list.exists():
        recipe.average_rating = float(
            ratings_list.aggregate(Avg("rating"))["rating__avg"] or 0.0
        )
        recipe.rating_count = ratings_list.count()
    else:
        recipe.average_rating = 0
        recipe.rating_count = 0

    sort = request.GET.get("sort", "newest")

    comments = recipe.comments.filter(parent_comment__isnull=True)

    if sort == "top":
        comments = comments.annotate(num_likes=Count("likes")).order_by(
            "-num_likes", "-created_at", "-id"
        )
    elif sort == "oldest":
        comments = comments.order_by("created_at", "id")
    else:
        comments = comments.order_by("-created_at", "-id")

    user_rating_score = 0
    is_following_author = False
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(recipe=recipe, user=request.user).first()
        user_rating_score = user_rating.rating if user_rating else 0
        # Check if the current user follows the recipe author
        is_following_author = Follow.objects.filter(
            follower=request.user, following=recipe.author
        ).exists()

    context = {
        "recipe": recipe,
        "comments": comments,
        "sort": sort,
        "user_rating_score": user_rating_score,
        "is_following_author": is_following_author,
    }
    return render(request, "recipe_detail.html", context)

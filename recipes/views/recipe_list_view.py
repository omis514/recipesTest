# recipes/views/recipe_list_view.py

from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch, Q, Avg
from recipes.models import Recipe, Comment


@login_required
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
            top_comment_prefetch, "comments", "ratings"  # Also get all comments for counting
        )
        .annotate(total_comments=Count("comments", distinct=True),
                  average_rating=Avg("ratings__rating"),
                  rating_count=Count("ratings", distinct=True)
                  )
    )

    # Filter by difficulty if requested
    difficulty = request.GET.get("difficulty")
    if difficulty:
        recipes = recipes.filter(difficulty=difficulty)

    # Filter by spiceness if requested
    spiceness = request.GET.get("spiceness")
    if spiceness:
        recipes = recipes.filter(spiceness=spiceness)

    # Filter by cuisine if requested
    cuisine = request.GET.get("cuisine")
    if cuisine:
        recipes = recipes.filter(cuisine=cuisine)

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
    elif sort_by == "rating":
        recipes = recipes.order_by("-average_rating", "-rating_count")
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
        "spicenesses": Recipe.Spiceness.choices,
        "cuisines": Recipe.Cuisine.choices,
        "selected_difficulty": difficulty,
        "selected_spiceness": spiceness,
        "selected_cuisine": cuisine,
        "search_term": search,
        "sort_by": sort_by,
    }
    return render(request, "recipe_list.html", context)

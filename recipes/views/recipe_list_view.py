# recipes/views/recipe_list_view.py

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch, Q, Avg
from django.urls import reverse
from django.contrib import messages
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

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
        .prefetch_related(top_comment_prefetch, "comments", "ratings", "favorites")
        .annotate(
            total_comments=Count("comments", distinct=True),
            average_rating=Avg("ratings__rating"),
            rating_count=Count("ratings", distinct=True),
        )
    )

    # Filter by difficulty if requested
    difficulty = request.GET.get("difficulty")
    if difficulty:
        recipes = recipes.filter(difficulty=difficulty)

    # Filter by spiciness if requested
    spiciness = request.GET.get("spiciness")
    if spiciness:
        recipes = recipes.filter(spiciness=spiciness)

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
        "spicinesses": Recipe.Spiciness.choices,
        "cuisines": Recipe.Cuisine.choices,
        "selected_difficulty": difficulty,
        "selected_spiciness": spiciness,
        "selected_cuisine": cuisine,
        "search_term": search,
        "sort_by": sort_by,
    }
    return render(request, "recipe_list.html", context)


class RecipeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating an existing recipe. Only author or staff can edit."""

    model = Recipe
    template_name = "recipe_create.html"
    # FIXED: Remove prep_time fields that don't exist in your Recipe model
    fields = [
        "title",
        "description",
        "difficulty",
        "spiciness",
        "cuisine",
        "vegetarian",
        "image",
    ]

    def test_func(self):
        """Check if user is the recipe author or staff"""
        recipe = self.get_object()
        return self.request.user == recipe.author or self.request.user.is_staff

    def get_success_url(self):
        """Redirect to recipe detail page after successful update"""
        messages.success(
            self.request, f'Recipe "{self.object.title}" has been updated!'
        )
        return reverse("recipe_detail", kwargs={"pk": self.object.pk})


@login_required
def delete_recipe(request, pk):
    """Delete a recipe. Only author or staff can delete."""
    recipe = get_object_or_404(Recipe, pk=pk)

    # Check permissions
    if request.user != recipe.author and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this recipe.")
        return redirect("recipe_detail", pk=pk)

    # Only allow POST requests for deletion (security)
    if request.method == "POST":
        recipe_title = recipe.title
        recipe.delete()
        messages.success(request, f'Recipe "{recipe_title}" has been deleted.')
        return redirect("recipe_list")

    # If not POST, redirect to detail page
    messages.warning(request, "Invalid request method.")
    return redirect("recipe_detail", pk=pk)

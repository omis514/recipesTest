# recipes/views/recipe_list_view.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q, Avg
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import UpdateView

from recipes.forms import RecipeForm, IngredientForm, InstructionForm
from recipes.models import Recipe, Comment, Ingredient, Instruction


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
        .filter(Q(visibility=Recipe.Visibility.PUBLIC) | Q(author=request.user))
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

    # Process recipes to add top comment and favorite status
    for recipe in page_obj.object_list:
        # Add top comment
        recipe.top_comment = (
            recipe.top_comment_list[0]
            if hasattr(recipe, "top_comment_list") and recipe.top_comment_list
            else None
        )

        # Add favorite status for current user
        recipe.is_favorited = request.user in recipe.favorites.all()

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


@login_required
def toggle_favorite(request, pk):
    """Toggle favorite status for a recipe (add/remove from favorites)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    recipe = get_object_or_404(Recipe, pk=pk)
    user = request.user

    # Check if user has already favorited this recipe
    if user in recipe.favorites.all():
        recipe.favorites.remove(user)
        user.recipes_favourited_num -= 1
        is_favorited = False
        message = f'Removed "{recipe.title}" from favorites'
    else:
        recipe.favorites.add(user)
        user.recipes_favourited_num += 1
        is_favorited = True
        message = f'Added "{recipe.title}" to favorites'

    # Calculate preferred spiciness based on all favorited recipes
    favorited_recipes = user.favorite_recipes.all()
    if favorited_recipes.exists():
        # Calculate average spiciness of all favorited recipes
        avg_spiciness = favorited_recipes.aggregate(Avg("spiciness"))["spiciness__avg"]
        user.preferred_spiceness = round(avg_spiciness, 2)
    else:
        # If no favorites, reset to default
        user.preferred_spiceness = 1.5

    user.save()

    # If it's an AJAX request, return JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {"success": True, "is_favorited": is_favorited, "message": message}
        )

    # Otherwise, redirect back (for non-AJAX fallback)
    messages.success(request, message)
    return redirect(request.META.get("HTTP_REFERER", "recipe_list"))


# Formsets for recipe editing (extra=0 since users can add more via JS buttons)
EditIngredientFormSet = inlineformset_factory(
    Recipe,
    Ingredient,
    form=IngredientForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

EditInstructionFormSet = inlineformset_factory(
    Recipe,
    Instruction,
    form=InstructionForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class RecipeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating an existing recipe. Only author or staff can edit."""

    model = Recipe
    form_class = RecipeForm
    template_name = "recipe_edit.html"

    def test_func(self):
        """Check if user is the recipe author or staff"""
        recipe = self.get_object()
        return self.request.user == recipe.author or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        """Add ingredient and instruction formsets to context."""
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()

        if self.request.method == "POST":
            context["ingredient_formset"] = EditIngredientFormSet(
                self.request.POST, self.request.FILES, instance=recipe
            )
            context["instruction_formset"] = EditInstructionFormSet(
                self.request.POST, self.request.FILES, instance=recipe
            )
        else:
            context["ingredient_formset"] = EditIngredientFormSet(instance=recipe)
            context["instruction_formset"] = EditInstructionFormSet(instance=recipe)

        # Context for shared form partial
        context["form_action"] = reverse("edit_recipe", kwargs={"pk": recipe.pk})
        context["cancel_url"] = reverse("recipe_detail", kwargs={"pk": recipe.pk})
        context["submit_text"] = "Save Changes"
        context["is_edit"] = True

        return context

    def form_valid(self, form):
        """Handle valid recipe form submissions."""
        recipe = self.get_object()

        ingredient_formset = EditIngredientFormSet(
            self.request.POST, self.request.FILES, instance=recipe
        )
        instruction_formset = EditInstructionFormSet(
            self.request.POST, self.request.FILES, instance=recipe
        )

        if ingredient_formset.is_valid() and instruction_formset.is_valid():
            self.object = form.save()
            ingredient_formset.save()
            instruction_formset.save()
            messages.success(
                self.request, f'Recipe "{self.object.title}" has been updated!'
            )
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submissions."""
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        """Redirect to recipe detail page after successful update"""
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

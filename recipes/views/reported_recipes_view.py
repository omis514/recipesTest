from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Prefetch
from django.shortcuts import render, get_object_or_404
from recipes.models import Report, Recipe


def staff_required(user):
    """Check if user is staff or superuser."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(staff_required)
def reported_recipes_list(request):
    """
    Display a paginated list of reported recipes grouped by recipe,
    showing the number of reports.

    This view is restricted to staff members and superusers only.
    """
    # Get recipes that have been reported, with report count
    # Order by most reported first
    reports_prefetch = Prefetch(
        "reports",
        queryset=Report.objects.select_related("reporter").order_by("-created_at"),
        to_attr="ordered_reports",
    )

    recipes_with_reports = (
        Recipe.objects.filter(reports__isnull=False)
        .select_related("author")
        .prefetch_related(reports_prefetch)
        .annotate(report_count=Count("reports"))
        .distinct()
        .order_by("-report_count", "title", "id")
    )

    paginator = Paginator(recipes_with_reports, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "reported_recipes.html",
        {
            "page_obj": page_obj,
        },
    )


@login_required
@user_passes_test(staff_required)
def recipe_reports_detail(request, recipe_id):
    """
    Display all reports for a specific recipe.

    This view is restricted to staff members and superusers only.
    """
    recipe = get_object_or_404(Recipe.objects.select_related("author"), pk=recipe_id)

    # Get all reports for this recipe, ordered by most recent first
    reports = (
        Report.objects.filter(recipe=recipe)
        .select_related("reporter")
        .order_by("-created_at")
    )

    paginator = Paginator(reports, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "recipe_reports_detail.html",
        {
            "recipe": recipe,
            "page_obj": page_obj,
        },
    )

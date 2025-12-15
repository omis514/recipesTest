from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import (
    Count,
    Q,
    F,
    FloatField,
    Case,
    When,
    Value,
    ExpressionWrapper,
)
from django.shortcuts import render, get_object_or_404, redirect

from recipes.models import User


def staff_required(user):
    """Check if user is staff or superuser."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(staff_required)
def user_list(request):
    """
    Display a paginated list of all users with their information.

    This view is restricted to staff members and superusers only.
    """

    users_list = (
        User.objects.annotate(
            total_recipes=Count("recipes", distinct=True),
            reported_recipes=Count(
                "recipes", filter=Q(recipes__reports__isnull=False), distinct=True
            ),
        )
        .annotate(
            report_percentage=Case(
                When(total_recipes=0, then=Value(0.0)),
                default=ExpressionWrapper(
                    F("reported_recipes") * 100.0 / F("total_recipes"),
                    output_field=FloatField(),
                ),
                output_field=FloatField(),
            )
        )
        .order_by("-report_percentage", "last_name", "first_name", "id")
    )

    paginator = Paginator(users_list, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(request, "user_list.html", {"page_obj": page_obj})


@login_required
@user_passes_test(staff_required)
def toggle_user_active_status(request, user_id):
    """
    Toggle the is_active status of a user.
    Restricted to staff members and superusers.
    """
    user_to_toggle = get_object_or_404(User, id=user_id)

    if user_to_toggle == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect("user_list")

    user_to_toggle.is_active = not user_to_toggle.is_active
    user_to_toggle.save()

    status = "activated" if user_to_toggle.is_active else "deactivated"
    messages.success(request, f"User {user_to_toggle.username} has been {status}.")

    return redirect("user_list")

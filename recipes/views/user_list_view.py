from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.shortcuts import render
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

    users_list = User.objects.annotate(recipe_count=Count("recipes")).order_by(
        "last_name", "first_name", "id"
    )

    paginator = Paginator(users_list, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "user_list.html",
        {
            "page_obj": page_obj,
        },
    )

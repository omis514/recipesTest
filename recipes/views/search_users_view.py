# recipes/views/search_users_view.py  (or wherever your view lives)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from recipes.models import User, Follow


@login_required
def search_users(request):
    """Display all users in a paginated table (50 per page)."""

    # Get all users
    users = User.objects.all()

    # Pagination — 25 users per page
    paginator = Paginator(users, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ---- FOLLOW STATE PRECOMPUTATION ----

    # Get a set of IDs the current user is following
    following_ids = set(
        Follow.objects.filter(follower=request.user).values_list(
            "following_id", flat=True
        )
    )

    # Add helper "is_followed" attribute to each user
    for u in page_obj.object_list:
        u.is_followed = u.id in following_ids

    # --------------------------------------

    # Send paginated users to template
    context = {
        "page_obj": page_obj,
    }

    return render(request, "search_users.html", context)

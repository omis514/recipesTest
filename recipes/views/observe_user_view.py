from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from recipes.models import User, Follow
from django.shortcuts import render


@login_required
def observeProfile(request, username):

    if username == request.user.username:
        return redirect("user_profile")

    target_user = get_object_or_404(User, username=username)

    # Same pattern as search_users
    following_ids = set(
        Follow.objects.filter(follower=request.user).values_list(
            "following_id", flat=True
        )
    )

    # Add is_followed attribute so follow_button.html works
    target_user.is_followed = target_user.id in following_ids

    context = {
        "target_user": target_user,
    }

    return render(request, "observe_user.html", context)

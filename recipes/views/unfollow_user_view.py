from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from recipes.models import User, Follow


@login_required
def unfollow_user(request, username):
    """Remove a follow relationship."""
    target = get_object_or_404(User, username=username)
    user = request.user

    try:
        relation = Follow.objects.get(follower=user, following=target)
        relation.delete()
        messages.success(request, f"You unfollowed {target.username}.")

    except Follow.DoesNotExist:
        messages.info(request, f"You were not following {target.username}.")

    return redirect(request.META.get("HTTP_REFERER", "/"))

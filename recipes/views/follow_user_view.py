from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from recipes.models import User, Follow


@login_required
def follow_user(request, username):
    """Create a follow relationship."""
    target = get_object_or_404(User, username=username)
    user = request.user

    # Prevent following yourself
    if user == target:
        messages.error(request, "You cannot follow yourself.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Prevent duplicate follows
    follow_exists = Follow.objects.filter(follower=user, following=target).exists()
    if follow_exists:
        messages.info(request, f"You are already following {target.username}.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Create follow relationship
    Follow.objects.create(follower=user, following=target)
    messages.success(request, f"You are now following {target.username}!")

    return redirect(request.META.get("HTTP_REFERER", "/"))

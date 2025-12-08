from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

from recipes.models import User, Follow


@login_required
def remove_follower(request, username):
    """Remove someone who is following the current user."""
    follower = get_object_or_404(User, username=username)
    user = request.user

    try:
        # Here THEY follow YOU (opposite of unfollow_user)
        relation = Follow.objects.get(follower=follower, following=user)
        relation.delete()
        messages.success(
            request,
            f"{follower.username} has been removed from your followers.",
        )
    except Follow.DoesNotExist:
        messages.info(
            request,
            f"{follower.username} is not currently following you.",
        )

    # Go back to the page the user came from (e.g. profile page)
    return redirect(request.META.get("HTTP_REFERER", "/"))

# recipes/views/comment_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from recipes.models import Recipe, Comment


@login_required
@require_POST
def add_comment(request, recipe_pk):
    """Add a comment or reply using the unified Comment model."""
    recipe = get_object_or_404(Recipe, pk=recipe_pk)

    content = request.POST.get("content", "").strip()
    parent_comment_id = request.POST.get("parent_comment_id", "").strip()
    reply_to_user = request.POST.get("reply_to_user", "").strip()

    if not content:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Comment cannot be empty."})
        messages.error(request, "Comment cannot be empty.")
        return redirect("recipe_detail", pk=recipe_pk)

    parent_comment = None
    reply_to = None

    # If replying
    if parent_comment_id:
        parent_comment = Comment.objects.filter(pk=parent_comment_id).first()

    # If @mention
    if reply_to_user:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        reply_to = User.objects.filter(username=reply_to_user).first()

    # Create unified comment
    comment = Comment.objects.create(
        recipe=recipe,
        author=request.user,
        content=content,
        parent_comment=parent_comment,
        reply_to=reply_to,
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "success": True,
                "comment_id": comment.pk,
                "content": comment.content,
                "author": comment.author.username,
                "parent_comment": parent_comment.pk if parent_comment else None,
            }
        )

    return redirect("recipe_detail", pk=recipe_pk)


@login_required
@require_POST
def like_comment(request, comment_pk):
    """Like/unlike any comment (top-level or reply)."""
    comment = get_object_or_404(Comment, pk=comment_pk)

    if comment.likes.filter(pk=request.user.pk).exists():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {"success": True, "liked": liked, "like_count": comment.likes.count()}
        )

    return redirect("recipe_detail", pk=comment.recipe.pk)


@login_required
@require_POST
def delete_comment(request, comment_pk):
    """Delete any comment (or reply)."""
    comment = get_object_or_404(Comment, pk=comment_pk)
    recipe_pk = comment.recipe.pk

    if comment.author != request.user and not request.user.is_staff:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Permission denied."})
        return redirect("recipe_detail", pk=recipe_pk)

    comment.delete()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True})

    return redirect("recipe_detail", pk=recipe_pk)

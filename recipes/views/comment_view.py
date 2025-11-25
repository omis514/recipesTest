# recipes/views/comment_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from recipes.models import Recipe, Comment, CommentReply


@login_required
@require_POST
def add_comment(request, recipe_pk):
    """Add a comment to a recipe."""
    recipe = get_object_or_404(Recipe, pk=recipe_pk)
    content = request.POST.get("content", "").strip()

    if content:
        comment = Comment.objects.create(
            recipe=recipe, author=request.user, content=content
        )
        messages.success(request, "Your comment has been added!")

        # Return JSON for AJAX requests
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "comment_id": comment.pk,
                    "author": comment.author.username,
                    "content": comment.content,
                    "created_at": comment.created_at.strftime("%d %b %Y"),
                    "like_count": 0,
                }
            )
    else:
        messages.error(request, "Comment cannot be empty.")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Comment cannot be empty."})

    return redirect("recipe_detail", pk=recipe_pk)


@login_required
@require_POST
def like_comment(request, comment_pk):
    """Toggle like on a comment."""
    comment = get_object_or_404(Comment, pk=comment_pk)

    if comment.likes.filter(pk=request.user.pk).exists():
        # Unlike
        comment.likes.remove(request.user)
        liked = False
    else:
        # Like
        comment.likes.add(request.user)
        liked = True

    # Return JSON response for AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {"success": True, "liked": liked, "like_count": comment.like_count}
        )

    return redirect("recipe_detail", pk=comment.recipe.pk)


@login_required
@require_POST
def delete_comment(request, comment_pk):
    """Delete a comment (only by author or admin)."""
    comment = get_object_or_404(Comment, pk=comment_pk)
    recipe_pk = comment.recipe.pk

    if comment.author == request.user or request.user.is_staff:
        comment.delete()
        messages.success(request, "Comment deleted successfully.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
    else:
        messages.error(request, "You cannot delete this comment.")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Permission denied."})

    return redirect("recipe_detail", pk=recipe_pk)


@login_required
@require_POST
def reply_to_comment(request, comment_pk):
    """Add a reply to a comment."""
    comment = get_object_or_404(Comment, pk=comment_pk)
    content = request.POST.get("content", "").strip()

    if content:
        reply = CommentReply.objects.create(
            comment=comment, author=request.user, content=content
        )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "reply_id": reply.pk,
                    "author": reply.author.username,
                    "content": reply.content,
                    "created_at": reply.created_at.strftime("%d %b %Y %H:%M"),
                }
            )

        messages.success(request, "Reply added successfully.")
    else:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Reply cannot be empty."})
        messages.error(request, "Reply cannot be empty.")

    return redirect("recipe_detail", pk=comment.recipe.pk)


def recipe_comments_api(request, recipe_pk):
    """API endpoint to get all comments for a recipe (for AJAX loading)."""
    recipe = get_object_or_404(Recipe, pk=recipe_pk)
    comments = (
        recipe.comments.select_related("author")
        .prefetch_related("likes", "replies__author")
        .order_by("-created_at")
    )

    # Pagination
    paginator = Paginator(comments, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    comments_data = []
    for comment in page_obj:
        comment_dict = {
            "id": comment.pk,
            "author": comment.author.username,
            "content": comment.content,
            "created_at": comment.created_at.strftime("%d %b %Y %H:%M"),
            "like_count": comment.like_count,
            "is_liked": (
                comment.is_liked_by(request.user)
                if request.user.is_authenticated
                else False
            ),
            "can_delete": comment.author == request.user or request.user.is_staff,
            "replies": [],
        }

        for reply in comment.replies.all():
            comment_dict["replies"].append(
                {
                    "id": reply.pk,
                    "author": reply.author.username,
                    "content": reply.content,
                    "created_at": reply.created_at.strftime("%d %b %Y %H:%M"),
                }
            )

        comments_data.append(comment_dict)

    return JsonResponse(
        {
            "success": True,
            "comments": comments_data,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
        }
    )

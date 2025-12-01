# recipes/views/comment_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from recipes.models import Recipe, Comment
import json

User = get_user_model()


@login_required
@require_POST
def add_comment(request, recipe_pk):
    """Add a new comment or reply to a recipe with proper AJAX support."""
    recipe = get_object_or_404(Recipe, pk=recipe_pk)
    content = request.POST.get("content", "").strip()
    parent_comment_id = request.POST.get("parent_comment_id", "").strip()
    reply_to_username = request.POST.get("reply_to_user", "").strip()

    if not content:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Comment cannot be empty"})
        messages.error(request, "Comment cannot be empty.")
        return redirect("recipe_detail", pk=recipe_pk)

    comment_data = {
        "recipe": recipe,
        "author": request.user,
        "content": content,
    }

    # Handle nested reply
    if parent_comment_id:
        try:
            parent = Comment.objects.get(pk=int(parent_comment_id))
            comment_data["parent_comment"] = parent
        except (Comment.DoesNotExist, ValueError):
            pass

    # Handle @mention reply_to
    if reply_to_username:
        # Remove @ if present in username
        clean_username = reply_to_username.lstrip("@")
        target_user = User.objects.filter(username=clean_username).first()
        if not target_user:
            # Try with @ prefix (based on your model)
            target_user = User.objects.filter(username=f"@{clean_username}").first()
        if target_user:
            comment_data["reply_to"] = target_user

    comment = Comment.objects.create(**comment_data)

    # For AJAX requests, return comprehensive data
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        response_data = {
            "success": True,
            "comment": {
                "id": comment.pk,
                "author": comment.author.username.lstrip("@"),  # Remove @ for display
                "author_display": comment.author.get_full_name()
                or comment.author.username.lstrip("@"),
                "content": content,
                "formatted_content": (
                    comment.get_formatted_content()
                    if hasattr(comment, "get_formatted_content")
                    else content
                ),
                "created_at": comment.created_at.strftime("%d %b %Y %H:%M"),
                "like_count": 0,
                "is_liked": False,
                "can_delete": True,  # User just created it
                "reply_to": (
                    comment.reply_to.username.lstrip("@") if comment.reply_to else None
                ),
                "is_reply": comment.parent_comment is not None,
                "parent_comment_id": (
                    comment.parent_comment.pk if comment.parent_comment else None
                ),
            },
        }
        return JsonResponse(response_data)

    messages.success(request, "Comment added successfully.")
    return redirect("recipe_detail", pk=recipe_pk)


@login_required
@require_POST
def like_comment(request, comment_pk):
    """Toggle like on a comment with proper response."""
    comment = get_object_or_404(Comment, pk=comment_pk)

    if comment.likes.filter(pk=request.user.pk).exists():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {"success": True, "liked": liked, "like_count": comment.like_count}
        )

    return redirect("recipe_detail", pk=comment.recipe.pk)


@login_required
@require_POST
def delete_comment(request, comment_pk):
    """Delete a comment with proper authorization check."""
    comment = get_object_or_404(Comment, pk=comment_pk)
    recipe_pk = comment.recipe.pk

    # Check permissions
    if comment.author != request.user and not request.user.is_staff:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "error": "You don't have permission to delete this comment.",
                },
                status=403,
            )
        messages.error(request, "You cannot delete this comment.")
        return redirect("recipe_detail", pk=recipe_pk)

    # Delete the comment
    comment.delete()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True})

    messages.success(request, "Comment deleted successfully.")
    return redirect("recipe_detail", pk=recipe_pk)


def get_user_mentions(request):
    """API endpoint for @ mention autocomplete."""
    query = request.GET.get("q", "")

    if len(query) < 2:
        return JsonResponse({"users": []})

    # Search for users (handle both with and without @ prefix)
    users = User.objects.filter(username__icontains=query).values(
        "username", "first_name", "last_name"
    )[:10]

    user_list = []
    for user in users:
        username = user["username"].lstrip("@")  # Remove @ for display
        full_name = f"{user['first_name']} {user['last_name']}".strip()
        user_list.append(
            {
                "username": username,
                "display_name": full_name if full_name else username,
            }
        )

    return JsonResponse({"users": user_list})


def recipe_comments_api(request, recipe_pk):
    """API endpoint to get all comments for a recipe."""
    recipe = get_object_or_404(Recipe, pk=recipe_pk)

    # Get only top-level comments (no parent)
    comments = (
        recipe.comments.filter(parent_comment__isnull=True)
        .select_related("author", "reply_to")
        .prefetch_related(
            "likes", "replies__author", "replies__reply_to", "replies__likes"
        )
        .order_by("-created_at")
    )

    # Pagination
    paginator = Paginator(comments, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    comments_data = []
    for comment in page_obj:
        # Clean username (remove @ if present)
        author_username = comment.author.username.lstrip("@")

        comment_dict = {
            "id": comment.pk,
            "author": author_username,
            "author_display": comment.author.get_full_name() or author_username,
            "content": comment.content,
            "formatted_content": (
                comment.get_formatted_content()
                if hasattr(comment, "get_formatted_content")
                else comment.content
            ),
            "created_at": comment.created_at.strftime("%d %b %Y %H:%M"),
            "like_count": comment.like_count,
            "is_liked": (
                comment.is_liked_by(request.user)
                if request.user.is_authenticated
                else False
            ),
            "can_delete": comment.author == request.user or request.user.is_staff,
            "reply_to": (
                comment.reply_to.username.lstrip("@") if comment.reply_to else None
            ),
            "is_reply": False,
            "replies": [],
        }

        # Add nested replies
        for reply in comment.replies.all():
            reply_author = reply.author.username.lstrip("@")
            comment_dict["replies"].append(
                {
                    "id": reply.pk,
                    "author": reply_author,
                    "author_display": reply.author.get_full_name() or reply_author,
                    "content": reply.content,
                    "formatted_content": (
                        reply.get_formatted_content()
                        if hasattr(reply, "get_formatted_content")
                        else reply.content
                    ),
                    "created_at": reply.created_at.strftime("%d %b %Y %H:%M"),
                    "like_count": reply.like_count,
                    "is_liked": (
                        reply.is_liked_by(request.user)
                        if request.user.is_authenticated
                        else False
                    ),
                    "can_delete": reply.author == request.user or request.user.is_staff,
                    "reply_to": (
                        reply.reply_to.username.lstrip("@") if reply.reply_to else None
                    ),
                    "is_reply": True,
                }
            )

        # Sort replies by created_at (oldest first for replies)
        comment_dict["replies"].sort(key=lambda x: x["created_at"])
        comments_data.append(comment_dict)

    return JsonResponse(
        {
            "success": True,
            "comments": comments_data,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
            "total_comments": recipe.comments.count(),
        }
    )

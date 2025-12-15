# recipes/views/comment_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.db import transaction
from recipes.models import Recipe, Comment
from recipes.models import Recipe, Comment, Rating
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

    # Validation
    if not content:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"success": False, "error": "Comment cannot be empty"}, status=400
            )
        messages.error(request, "Comment cannot be empty.")
        return redirect("recipe_detail", pk=recipe_pk)

    # Character limit validation (optional but recommended)
    if len(content) > 1000:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "error": "Comment is too long (max 1000 characters)",
                },
                status=400,
            )
        messages.error(request, "Comment is too long.")
        return redirect("recipe_detail", pk=recipe_pk)

    comment_data = {
        "recipe": recipe,
        "author": request.user,
        "content": content,
    }

    # Handle nested reply with validation
    if parent_comment_id:
        try:
            parent = Comment.objects.get(pk=int(parent_comment_id))
            # Ensure parent belongs to same recipe
            if parent.recipe.pk != recipe.pk:
                raise Comment.DoesNotExist
            comment_data["parent_comment"] = parent
        except (Comment.DoesNotExist, ValueError):
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "error": "Invalid parent comment"}, status=400
                )
            messages.error(request, "Invalid parent comment.")
            return redirect("recipe_detail", pk=recipe_pk)

    # Handle @mention reply_to with improved logic
    if reply_to_username:
        # Clean username - remove @ and whitespace
        clean_username = reply_to_username.lstrip("@").strip()

        # Try to find user
        try:
            target_user = User.objects.get(username=clean_username)
            comment_data["reply_to"] = target_user
        except User.DoesNotExist:
            # Try with @ prefix if your usernames include it
            try:
                target_user = User.objects.get(username=f"@{clean_username}")
                comment_data["reply_to"] = target_user
            except User.DoesNotExist:
                # Don't fail - just skip the mention
                pass

    # Create comment with transaction for safety
    try:
        with transaction.atomic():
            comment = Comment.objects.create(**comment_data)
    except Exception as e:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"success": False, "error": "Failed to create comment"}, status=500
            )
        messages.error(request, "Failed to create comment.")
        return redirect("recipe_detail", pk=recipe_pk)

    author_rating = Rating.objects.filter(recipe=recipe, user=comment.author).first()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        response_data = {
            "success": True,
            "comment": {
                "id": comment.pk,
                "author": comment.author.username.lstrip("@"),
                "author_display": (
                    comment.author.get_full_name()
                    or comment.author.username.lstrip("@")
                ),
                "author_gravatar": comment.author.mini_gravatar(),
                "content": content,
                "created_at": int(
                    comment.created_at.timestamp()
                ),  # Unix timestamp for JS
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
                "author_rating": author_rating.rating if author_rating else 0,
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

    # Toggle like
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

    # Delete the comment (CASCADE will delete replies)
    comment.delete()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True})

    messages.success(request, "Comment deleted successfully.")
    return redirect("recipe_detail", pk=recipe_pk)


@require_http_methods(["GET"])
def get_user_mentions(request):
    """API endpoint for @ mention autocomplete."""
    query = request.GET.get("q", "").strip()

    # Minimum query length
    if len(query) < 2:
        return JsonResponse({"users": []})

    # Search for users (handle both with and without @ prefix)
    # Remove @ from query if present
    search_query = query.lstrip("@")

    users = User.objects.filter(username__icontains=search_query).values(
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


@require_http_methods(["GET"])
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
            "created_at": int(comment.created_at.timestamp()),  # Unix timestamp
            "like_count": comment.like_count,
            "is_liked": (
                comment.likes.filter(pk=request.user.pk).exists()
                if request.user.is_authenticated
                else False
            ),
            "can_delete": (
                comment.author == request.user or request.user.is_staff
                if request.user.is_authenticated
                else False
            ),
            "reply_to": (
                comment.reply_to.username.lstrip("@") if comment.reply_to else None
            ),
            "is_reply": False,
            "replies": [],
        }

        # Add nested replies
        for reply in comment.replies.all().order_by("created_at"):
            reply_author = reply.author.username.lstrip("@")
            comment_dict["replies"].append(
                {
                    "id": reply.pk,
                    "author": reply_author,
                    "author_display": reply.author.get_full_name() or reply_author,
                    "content": reply.content,
                    "created_at": int(reply.created_at.timestamp()),
                    "like_count": reply.like_count,
                    "is_liked": (
                        reply.likes.filter(pk=request.user.pk).exists()
                        if request.user.is_authenticated
                        else False
                    ),
                    "can_delete": (
                        reply.author == request.user or request.user.is_staff
                        if request.user.is_authenticated
                        else False
                    ),
                    "reply_to": (
                        reply.reply_to.username.lstrip("@") if reply.reply_to else None
                    ),
                    "is_reply": True,
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
            "total_comments": recipe.comments.count(),
        }
    )

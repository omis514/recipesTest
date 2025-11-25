# recipes/models/comment.py

from django.db import models
from django.conf import settings
from .recipe import Recipe


class Comment(models.Model):
    """Model for recipe comments with like functionality."""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipe_comments",
    )
    content = models.TextField(
        max_length=500, help_text="Share your thoughts about this recipe"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Like functionality
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="liked_comments", blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipe", "-created_at"]),
            models.Index(fields=["recipe", "author"]),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.recipe.title}"

    @property
    def like_count(self):
        """Return the number of likes."""
        return self.likes.count()

    def is_liked_by(self, user):
        """Check if a specific user has liked this comment."""
        if user.is_authenticated:
            return self.likes.filter(pk=user.pk).exists()
        return False

    def get_display_content(self, max_length=100):
        """Get truncated content for preview."""
        if len(self.content) > max_length:
            return f"{self.content[:max_length]}..."
        return self.content


class CommentReply(models.Model):
    """Model for replies to comments."""

    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="replies"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_replies",
    )
    content = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "Comment replies"

    def __str__(self):
        return f"Reply by {self.author.username}"

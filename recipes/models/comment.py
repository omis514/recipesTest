from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from .recipe import Recipe
import re


class Comment(models.Model):
    """Model for recipe comments supporting likes, mentions, and nested replies."""

    # The recipe this comment belongs to
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    # The user who created the comment
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipe_comments",
    )

    # Main comment text
    content = models.TextField(
        max_length=500,
        help_text="Share your thoughts about this recipe",
    )

    # Parent comment for nested replies.
    # If None → this is a top-level comment.
    # If set → this comment is a reply to another comment.
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )

    # The user that this comment is replying to (first @mention)
    reply_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mentions",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Users who liked this comment
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_comments",
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]  # newest comments first by default
        indexes = [
            models.Index(fields=["recipe", "-created_at"]),
            models.Index(fields=["recipe", "author"]),
            models.Index(fields=["parent_comment"]),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.recipe.title}"

    # ----- Utility properties / methods -----

    @property
    def like_count(self):
        """Return the number of likes this comment has."""
        return self.likes.count()

    @property
    def is_reply(self):
        """Return True if this comment is a reply (i.e. has a parent comment)."""
        return self.parent_comment is not None

    def is_liked_by(self, user):
        """Check whether a given user has liked this comment."""
        if user.is_authenticated:
            return self.likes.filter(pk=user.pk).exists()
        return False

    def get_display_content(self, max_length=100):
        """
        Return a shortened preview version of the comment content.
        Used in recipe lists or summaries.
        """
        if len(self.content) > max_length:
            return f"{self.content[:max_length]}..."
        return self.content

    def get_formatted_content(self):
        """
        Return content with highlighted @mentions converted into HTML.
        Example:
            "Hello @alice"
        becomes:
            "Hello <span class='mention-tag'>@alice</span>"
        This HTML should be rendered using |safe in templates.
        """
        content = self.content
        pattern = r"@(\w+)"
        formatted = re.sub(
            pattern,
            r'<span class="mention-tag">@\1</span>',
            content,
        )
        return formatted

    def extract_mentions(self):
        """
        Extract all @username occurrences from comment content.
        Returns a list of usernames without the @ symbol.
        """
        pattern = r"@(\w+)"
        return re.findall(pattern, self.content)

    def clean(self):
        """Custom validation for the model."""
        super().clean()
        if self.content and len(self.content) > 500:
            raise ValidationError(
                {"content": "Comment content cannot exceed 500 characters."}
            )

    def save(self, *args, **kwargs):
        """
        Automatically set 'reply_to' based on the first @mention if not provided.
        The mention should match a username exactly (including the @ prefix).
        """
        # Only auto-set reply_to if it's not already set
        if not self.reply_to and self.content:
            mentions = self.extract_mentions()
            if mentions:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                # Add @ prefix since usernames in DB have it
                first_mention_username = f"@{mentions[0]}"
                try:
                    mentioned_user = User.objects.get(username=first_mention_username)
                    self.reply_to = mentioned_user
                except User.DoesNotExist:
                    pass  # User doesn't exist, leave reply_to as None

        super().save(*args, **kwargs)

    def get_author_rating(self):
        """Return the user's rating for a recipe"""
        from .rating import Rating

        rating = Rating.objects.filter(recipe=self.recipe, user=self.author).first()

        return rating.rating if rating else None

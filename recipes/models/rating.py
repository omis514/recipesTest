from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from .recipe import Recipe

class Rating(models.Model):
    """Model used for a rating."""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="ratings"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="given_ratings"
    )
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1, "Rating must be between 1 and 5"),
            MaxValueValidator(5, "Rating must be between 1 and 5")
        ],
        help_text="Score out of 5 for the recipe"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model options."""

        unique_together = ("recipe", "user")
        ordering = ["-created_at"]

    def __str__(self):
        """Return a string representation of the rating."""

        return f"{self.rating} Star rating by {self.user.username} for {self.recipe.title}"



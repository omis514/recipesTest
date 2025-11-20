from django.db import models
from django.conf import settings


class Recipe(models.Model):
    """Model used for a recipe."""

    class Difficulty(models.IntegerChoices):
        EASY = 1, "Easy"
        MEDIUM = 2, "Medium"
        HARD = 3, "Hard"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipes"
    )
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(blank=True, help_text="A description of the recipe.")
    difficulty = models.IntegerField(
        blank=False,
        choices=Difficulty.choices,
        default=Difficulty.EASY,
        help_text="Estimated difficulty of the recipe",
    )
    image = models.ImageField(
        upload_to="recipe/images",
        blank=True,
        null=True,
        help_text="An optional image for the recipe",
    )
    time = models.IntegerField(
        blank=False,
        default=30,
        help_text="Time taken to complete the recipe (in minutes)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model options."""

        ordering = ["-created_at"]

    def __str__(self):
        """Return the recipe title."""
        return self.title

    def get_time(self):
        minutes = self.time

        if minutes is None or minutes < 0:
            return "N/A"
        if minutes == 0:
            return "0 mins"

        if minutes < 60:
            return f"{minutes} mins"

        hours = minutes / 60
        return f"{hours:.1f} hrs"

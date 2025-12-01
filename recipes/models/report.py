from django.db import models
from django.conf import settings
from .recipe import Recipe


class Report(models.Model):
    """Model for reporting recipes with summary notes."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="reports",
        help_text="The recipe being reported",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_made",
        help_text="The user who made the report",
    )
    summary = models.TextField(
        max_length=1000,
        help_text="Summary or notes about why this recipe is being reported",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When the report was created"
    )

    class Meta:
        """Model options."""

        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipe", "-created_at"]),
            models.Index(fields=["reporter", "-created_at"]),
        ]

    def __str__(self):
        """Return a string representation of the report."""
        return f"Report by {self.reporter.username} on {self.recipe.title}"

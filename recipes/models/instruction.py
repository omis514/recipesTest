from django.db import models
from .recipe import Recipe


class Instruction(models.Model):
    """Model used to describe instructions.
    An instruction one step in a dish's recipe."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instructions",
    )
    step = models.IntegerField(
        blank=False, help_text="The step number of the instruction"
    )
    description = models.TextField(
        max_length=500, blank=False, help_text="The text of the instruction"
    )
    image = models.ImageField(
        upload_to="recipe/instructions",
        blank=True,
        null=True,
        help_text="An optional image for this instruction step",
    )

    class Meta:
        """Model options."""

        unique_together = ("recipe", "step")

    def __str__(self):
        """Return a string representation of the instruction."""
        if self.recipe:
            return f"Instruction {self.step} for {self.recipe.title}"
        return f"Instruction {self.step}"

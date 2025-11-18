from django.db import models
from .recipe import Recipe


class Ingredient(models.Model):
    """Model used for an ingredient."""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="ingredients"
    )
    name = models.CharField(
        max_length=100, blank=False, help_text="The name of the ingredient"
    )
    quantity = models.IntegerField(
        blank=True, null=True, help_text="The quantity of the ingredient"
    )
    unit = models.CharField(
        max_length=50, blank=True, help_text="The unit of measurement"
    )

    class Meta:
        """Model options."""

        unique_together = ("recipe", "name")
        ordering = ["id"]

    def __str__(self):
        string = ""

        if self.quantity or self.quantity == 0:
            string += str(self.quantity) + " "
        if self.unit:
            string += str(self.unit) + " "

        string += self.name

        return string

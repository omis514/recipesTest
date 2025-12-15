from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Recipe(models.Model):
    """Model used for a recipe."""

    class Difficulty(models.IntegerChoices):
        EASY = 1, "Easy"
        MEDIUM = 2, "Medium"
        HARD = 3, "Hard"

    class Spiciness(models.IntegerChoices):
        NOT_SPICY = 0, "Not Spicy"
        MILD = 1, "Mild"
        MEDIUM = 2, "Medium"
        HOT = 3, "Hot"
        VERY_HOT = 4, "Very Hot"
        ULTRA_HOT = 5, "ULTRA Hot"

    class Cuisine(models.IntegerChoices):
        World = 1, "World"
        BRITISH = 2, "British"
        FRENCH = 3, "French"
        ITALIAN = 4, "Italian"
        MEXICAN = 5, "Mexican"
        SPANISH = 6, "Spanish"
        Chinese = 7, "Chinese"
        Japanese = 8, "Japanese"
        Korean = 9, "Korean"
        Indian = 10, "Indian"
        Thai = 11, "Thai"
        Vietnamese = 12, "Vietnamese"
        Eastern_European = 13, "Eastern European"
        African = 14, "African"
        Carribbean = 15, "Carribbean"
        American = 16, "American"
        German = 17, "German"
        Greek = 18, "Greek"
        Middle_Eastern = 19, "Middle Eastern"
        Turkish = 20, "Turkish"
        Caucasian = 21, "Caucasian️"
        South_American = (
            22,
            "South American",
        )

    class Visibility(models.IntegerChoices):
        PUBLIC = 0, "Public"
        PRIVATE = 1, "Private"

    servings = models.IntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Number of servings this recipe makes",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipes"
    )
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(blank=True, help_text="A description of the recipe.")
    visibility = models.IntegerField(
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        help_text="Visibility of the recipe",
    )
    difficulty = models.IntegerField(
        blank=False,
        choices=Difficulty.choices,
        default=Difficulty.EASY,
        help_text="Estimated difficulty of the recipe",
    )
    spiciness = models.IntegerField(
        blank=False,
        null=False,
        help_text="The spiciness level of the recipe",
        choices=Spiciness.choices,
        default=Spiciness.NOT_SPICY,
    )
    cuisine = models.IntegerField(
        blank=False,
        null=False,
        help_text="The cuisine of the recipe",
        choices=Cuisine.choices,
        default=Cuisine.World,
    )
    vegetarian = models.BooleanField(
        default=False, help_text="Whether the recipe is vegetarian"
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
    favorites = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="favorite_recipes", blank=True
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

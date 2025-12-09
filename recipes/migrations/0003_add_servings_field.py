# Generated manually to fix missing servings column

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0002_add_bio_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="servings",
            field=models.IntegerField(
                default=4,
                help_text="Number of servings this recipe makes",
                validators=[
                    MinValueValidator(1),
                    MaxValueValidator(50),
                ],
            ),
        ),
    ]

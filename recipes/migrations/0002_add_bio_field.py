# Generated manually to fix missing bio column

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="bio",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]

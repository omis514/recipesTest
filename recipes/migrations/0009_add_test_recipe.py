from django.db import migrations
from django.conf import settings


def create_test_recipe(apps, schema_editor):
    return


def delete_test_recipe(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0008_instruction_image"),
    ]

    operations = [
        migrations.RunPython(create_test_recipe, delete_test_recipe),
    ]

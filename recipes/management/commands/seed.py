"""
Management command to seed the database with demo data.

This command creates a small set of named fixture users and then fills up
to ``USER_COUNT`` total users using Faker-generated data. Existing records
are left untouched—if a create fails (e.g., due to duplicates), the error
is swallowed and generation continues.
"""

import json
from faker import Faker
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.files import File
from recipes.models import User, Recipe, Ingredient, Instruction, Comment
from django.utils.dateparse import parse_datetime


user_fixtures = [
    {
        "username": "@johndoe",
        "email": "john.doe@example.org",
        "first_name": "John",
        "last_name": "Doe",
        "bio": "BlueJ addict. Amateur chef. Kölling enthusiast.",
    },
    {
        "username": "@janedoe",
        "email": "jane.doe@example.org",
        "first_name": "Jane",
        "last_name": "Doe",
        "bio": "Designer by day, baker by night.",
    },
    {
        "username": "@charlie",
        "email": "charlie.johnson@example.org",
        "first_name": "Charlie",
        "last_name": "Johnson",
        "bio": "I love hiking, gaming, and cooking cool things.",
    },
    {
        "username": "@FraserTest",
        "email": "k23163980@kcl.ac.uk",
        "first_name": "Fraser",
        "last_name": "Shimmins",
        "bio": "This is a test profile set up by Fraser to manually test features during development",
    },
]


class Command(BaseCommand):
    """
    Build automation command to seed the database with data.

    This command inserts a small set of known users (``user_fixtures``) and then
    repeatedly generates additional random users until ``USER_COUNT`` total users
    exist in the database. Each generated user receives the same default password.

    Attributes:
        USER_COUNT (int): Target total number of users in the database.
        DEFAULT_PASSWORD (str): Default password assigned to all created users.
        help (str): Short description shown in ``manage.py help``.
        faker (Faker): Locale-specific Faker instance used for random data.
    """

    USER_COUNT = 200
    DEFAULT_PASSWORD = "Password123"
    help = "Seeds the database with sample data"

    def __init__(self, *args, **kwargs):
        """Initialize the command with a locale-specific Faker instance."""
        super().__init__(*args, **kwargs)
        self.faker = Faker("en_GB")

    def handle(self, *args, **options):
        """
        Django entrypoint for the command.

        Runs the full seeding workflow and stores ``self.users`` for any
        post-processing or debugging (not required for operation).
        """
        self.create_users()
        self.users = User.objects.all()
        self.recipes_in_json_order = self.create_recipes_from_json()
        self.create_comments_from_json()

    def create_users(self):
        """
        Create fixture users and then generate random users up to USER_COUNT.

        The process is idempotent in spirit: attempts that fail (e.g., due to
        uniqueness constraints on username/email) are ignored and generation continues.
        """
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        """Attempt to create each predefined fixture user."""
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        """
        Generate random users until the database contains USER_COUNT users.

        Prints a simple progress indicator to stdout during generation.
        """
        user_count = User.objects.count()
        while user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end="\r")
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
        """
        Generate a single random user and attempt to insert it.

        Uses Faker for first/last names, then derives a simple username/email.
        """
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)
        username = create_username(first_name, last_name)
        bio = self.faker.text(max_nb_chars=400)

        self.try_create_user(
            {
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "bio": bio,
            }
        )

    def try_create_user(self, data):
        """
        Attempt to create a user and ignore any errors.

        Args:
            data (dict): Mapping with keys ``username``, ``email``,
                ``first_name``, and ``last_name``.
        """
        try:
            self.create_user(data)
        except:
            pass

    def create_user(self, data):
        """
        Create a user with the default password.

        Args:
            data (dict): Mapping with keys ``username``, ``email``,
                ``first_name``, and ``last_name``.
        """
        User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=Command.DEFAULT_PASSWORD,
            first_name=data["first_name"],
            last_name=data["last_name"],
            bio=data["bio"],
        )

    def create_recipes_from_json(self):
        """
        Create recipes from the fake_recipes.json file.

        Reads recipe data from JSON and creates Recipe, Ingredient, and Instruction
        objects.

        Returns:
            list: List of Recipe objects in the same order as they appear in the JSON file.
        """
        recipes_in_order = []
        try:
            json_path = (
                settings.BASE_DIR
                / "static"
                / "json"
                / "fake_recipes"
                / "fake_recipes.json"
            )

            # Check if file exists
            if not json_path.exists():
                return recipes_in_order

            with open(json_path, "r", encoding="utf-8") as f:
                recipes_data = json.load(f)

            for recipe_data in recipes_data:
                recipe = self.create_recipe_from_data(recipe_data)
                if recipe:
                    recipes_in_order.append(recipe)

        except Exception as e:
            pass

        return recipes_in_order

    def create_recipe_from_data(self, recipe_data):
        """
        Create a single recipe from recipe data dictionary parsed from JSON.

        Returns:
            Recipe: The created or existing Recipe object, or None if creation failed.
        """
        try:
            author_username = recipe_data.get("author_username", "@johndoe")
            author = User.objects.filter(username=author_username).first()

            if not author:
                # If specified user doesn't exist, use the first available user
                author = User.objects.first()

            if not author:
                # No users available, skip recipe creation
                return None

            # Check if recipe already exists
            title = recipe_data.get("title")
            existing_recipe = Recipe.objects.filter(title=title).first()
            if existing_recipe:
                recipe = existing_recipe
            else:
                recipe = Recipe.objects.create(
                    author=author,
                    title=title,
                    description=recipe_data.get("description", ""),
                    vegetarian=recipe_data.get("vegetarian", False),
                    difficulty=recipe_data.get("difficulty", Recipe.Difficulty.EASY),
                    spiciness=recipe_data.get("spiciness", Recipe.Spiciness.NOT_SPICY),
                    cuisine=recipe_data.get("cuisine", Recipe.Cuisine.World),
                    time=recipe_data.get("time", 30),
                )

                # Handle image if provided
                image_filename = recipe_data.get("image")
                if image_filename:
                    self.add_recipe_image(recipe, image_filename)

            # Add ingredients (only if they don't already exist)
            for ing_data in recipe_data.get("ingredients", []):
                # Check if ingredient already exists
                existing_ing = Ingredient.objects.filter(
                    recipe=recipe,
                    name=ing_data.get("name", ""),
                    quantity=ing_data.get("quantity"),
                    unit=ing_data.get("unit", ""),
                ).first()
                if not existing_ing:
                    Ingredient.objects.create(
                        recipe=recipe,
                        name=ing_data.get("name", ""),
                        quantity=ing_data.get("quantity"),
                        unit=ing_data.get("unit", ""),
                    )

            # Add instructions (only if they don't already exist)
            for inst_data in recipe_data.get("instructions", []):
                step = inst_data.get("step")
                # Check if instruction for this step already exists
                existing_inst = Instruction.objects.filter(
                    recipe=recipe,
                    step=step,
                ).first()
                if not existing_inst:
                    Instruction.objects.create(
                        recipe=recipe,
                        step=step,
                        description=inst_data.get("description", ""),
                    )

            return recipe

        except Exception as e:
            return None

    def add_recipe_image(self, recipe, image_filename):
        """
        Copy image from static/images to media/recipe/images and assign to recipe.
        """
        try:
            # Source path in static/images
            source_path = settings.BASE_DIR / "static" / "images" / image_filename

            if not source_path.exists():
                print(f"Image file {image_filename} not found")
                return

            with open(source_path, "rb") as f:
                recipe.image.save(image_filename, File(f), save=True)

        except Exception as e:
            print(f"Error adding image {image_filename} to recipe {recipe.title}: {e}")
            pass

    def create_comments_from_json(self):
        """
        Create comments from the fake_comments.json file.

        Reads comment data from JSON and creates Comment objects with proper
        relationships (recipe, author, parent_comment, reply_to).
        """
        try:
            json_path = (
                settings.BASE_DIR
                / "static"
                / "json"
                / "fake_recipes"
                / "fake_comments.json"
            )

            # Check if file exists
            if not json_path.exists():
                return

            with open(json_path, "r", encoding="utf-8") as f:
                comments_data = json.load(f)

            # Use recipes in JSON order if available, otherwise fall back to database order
            recipes = (
                self.recipes_in_json_order
                if hasattr(self, "recipes_in_json_order") and self.recipes_in_json_order
                else list(Recipe.objects.all().order_by("id"))
            )
            users = list(User.objects.all().order_by("id"))

            # Create a mapping of user IDs to user objects for faster lookup
            users_by_id = {user.id: user for user in users}

            if not recipes or not users:
                return

            # First pass: create all top-level comments (no parent_comment)
            created_comments = {}

            for comment_data in comments_data:
                if comment_data.get("model") == "recipes.comment":
                    fields = comment_data.get("fields", {})
                    parent_comment_id = fields.get("parent_comment")

                    # Only create top-level comments in first pass
                    if not parent_comment_id:
                        comment = self.create_comment_from_data(
                            comment_data, created_comments, recipes, users, users_by_id
                        )
                        if comment:
                            pk = comment_data.get("pk")
                            if pk:
                                created_comments[pk] = comment

            # Second pass: create reply comments (with parent_comment)
            for comment_data in comments_data:
                if comment_data.get("model") == "recipes.comment":
                    fields = comment_data.get("fields", {})
                    parent_comment_id = fields.get("parent_comment")

                    # Only create reply comments in second pass
                    if parent_comment_id:
                        comment = self.create_comment_from_data(
                            comment_data, created_comments, recipes, users, users_by_id
                        )
                        if comment:
                            pk = comment_data.get("pk")
                            if pk:
                                created_comments[pk] = comment

        except Exception as e:
            print(f"Error creating comments: {e}")
            pass

    def create_comment_from_data(
        self, comment_data, created_comments, recipes, users, users_by_id
    ):
        """
        Create a single comment from comment data dictionary parsed from JSON.

        Args:
            comment_data (dict): Dictionary containing comment information from JSON.
            created_comments (dict): Dictionary mapping original PKs to created Comment objects.
            recipes (list): List of Recipe objects in the same order as they appear in the JSON file.
            users (list): List of User objects ordered by ID.
            users_by_id (dict): Dictionary mapping user IDs to User objects.

        Returns:
            Comment: The created comment object, or None if creation failed.
        """
        try:
            fields = comment_data.get("fields", {})

            # Get recipe by index (recipe_id - 1 to convert to 0-based index)
            recipe_id = fields.get("recipe")
            if recipe_id and recipe_id > 0 and recipe_id <= len(recipes):
                recipe = recipes[recipe_id - 1]
            else:
                return None

            # Get author by actual database ID first, then fall back to index
            author_id = fields.get("author")
            author = None
            if author_id:
                # Try to get by actual database ID
                author = users_by_id.get(author_id)
                # If not found, try index-based lookup as fallback
                if not author and author_id > 0 and author_id <= len(users):
                    author = users[author_id - 1]

            if not author:
                return None

            # Get parent comment if specified
            parent_comment = None
            parent_comment_id = fields.get("parent_comment")
            if parent_comment_id and parent_comment_id in created_comments:
                parent_comment = created_comments[parent_comment_id]

            # Get reply_to user by actual database ID first, then fall back to index
            reply_to = None
            reply_to_id = fields.get("reply_to")
            if reply_to_id:
                # Try to get by actual database ID
                reply_to = users_by_id.get(reply_to_id)
                # If not found, try index-based lookup as fallback
                if not reply_to and reply_to_id > 0 and reply_to_id <= len(users):
                    reply_to = users[reply_to_id - 1]

            # Parse timestamps
            created_at = None
            updated_at = None
            created_at_str = fields.get("created_at")
            updated_at_str = fields.get("updated_at")

            if created_at_str:
                created_at = parse_datetime(created_at_str)
            if updated_at_str:
                updated_at = parse_datetime(updated_at_str)

            # Check if comment already exists to avoid duplicates
            content = fields.get("content", "")
            existing_comment = Comment.objects.filter(
                recipe=recipe,
                author=author,
                content=content,
                parent_comment=parent_comment,
            ).first()

            if existing_comment:
                # Comment already exists, return it instead of creating a new one
                return existing_comment

            # Create the comment
            comment = Comment.objects.create(
                recipe=recipe,
                author=author,
                content=content,
                parent_comment=parent_comment,
                reply_to=reply_to,
            )

            # Update timestamps if provided (using update to bypass auto_now/auto_now_add)
            update_kwargs = {}
            if created_at:
                update_kwargs["created_at"] = created_at
            if updated_at:
                update_kwargs["updated_at"] = updated_at

            if update_kwargs:
                Comment.objects.filter(pk=comment.pk).update(**update_kwargs)
                # Refresh from database to get updated timestamps
                comment.refresh_from_db()

            return comment

        except Exception as e:
            print(f"Error creating comment: {e}")
            return None


def create_username(first_name, last_name):
    """
    Construct a simple username from first and last names.

    Args:
        first_name (str): Given name.
        last_name (str): Family name.

    Returns:
        str: A username in the form ``@{firstname}{lastname}`` (lowercased).
    """
    return "@" + first_name.lower() + last_name.lower()


def create_email(first_name, last_name):
    """
    Construct a simple example email address.

    Args:
        first_name (str): Given name.
        last_name (str): Family name.

    Returns:
        str: An email in the form ``{firstname}.{lastname}@example.org``.
    """
    return first_name + "." + last_name + "@example.org"

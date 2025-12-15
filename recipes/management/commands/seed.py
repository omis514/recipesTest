"""
Management command to seed the database with demo data.

This command creates a small set of named fixture users and then fills up
to ``USER_COUNT`` total users using Faker-generated data. Existing records
are left untouched—if a create fails (e.g., due to duplicates), the error
is swallowed and generation continues.
"""

import json
import random
from faker import Faker
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.files import File
from django.db.models import Count
from recipes.models import (
    User,
    Recipe,
    Ingredient,
    Instruction,
    Comment,
    Report,
    Follow,
    Rating,
)
from django.utils.dateparse import parse_datetime


user_fixtures = [
    {
        "username": "@johndoe",
        "email": "bronze6Demo1@outlook.com",
        "first_name": "John",
        "last_name": "Doe",
        "bio": "BlueJ addict. Amateur chef. Kölling enthusiast.",
    },
    {
        "username": "@janedoe",
        "email": "bronze6Demo2@outlook.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "bio": "Designer by day, baker by night.",
    },
    {
        "username": "@charliejohnson",
        "email": "bronze6Demo3@outlook.com",
        "first_name": "Charlie",
        "last_name": "Johnson",
        "bio": "I love hiking, gaming, and cooking cool things.",
    },
    {
        "username": "@sarahjohnson",
        "email": "bronze6Demo4@outlook.com",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "bio": "I love photography and cooking after work.",
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
        self.create_follow_relationships()
        self.generate_random_recipes()
        self.recipes_in_json_order = self.create_recipes_from_json()
        self.generate_random_comments()
        self.generate_random_ratings()
        self.create_comments_from_json()
        self.create_reports()

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

    def create_follow_relationships(self):
        """
        Create follow relationships so each user follows 3-5 random other users.

        Skips creating duplicate follows if they already exist.
        """
        users = list(User.objects.all())

        print("Seeding follow relationships...")
        total_users = len(users)

        for i, user in enumerate(users):
            print(f"Creating follows for user {i + 1}/{total_users}", end="\r")

            other_users = [
                u for u in users if u != user
            ]  # Get other users (exclude self)
            num_to_follow = random.randint(3, 5)

            # Randomly select users to follow
            users_to_follow = random.sample(other_users, num_to_follow)

            for target in users_to_follow:
                # Check if follow already exists to avoid duplicates
                if not Follow.objects.filter(follower=user, following=target).exists():
                    Follow.objects.create(follower=user, following=target)

        print("Follow relationships seeding complete.      ")

    RANDOM_RECIPE_COUNT = 500

    # Common ingredients for random recipe generation
    COMMON_INGREDIENTS = [
        "salt",
        "pepper",
        "olive oil",
        "butter",
        "garlic",
        "onion",
        "tomatoes",
        "chicken breast",
        "beef mince",
        "pork loin",
        "salmon fillet",
        "shrimp",
        "rice",
        "pasta",
        "bread",
        "flour",
        "sugar",
        "eggs",
        "milk",
        "cream",
        "cheese",
        "parmesan",
        "mozzarella",
        "cheddar",
        "feta",
        "carrots",
        "celery",
        "potatoes",
        "bell peppers",
        "mushrooms",
        "spinach",
        "broccoli",
        "zucchini",
        "aubergine",
        "green beans",
        "peas",
        "corn",
        "lemon",
        "lime",
        "orange",
        "apple",
        "banana",
        "berries",
        "basil",
        "oregano",
        "thyme",
        "rosemary",
        "parsley",
        "cilantro",
        "mint",
        "cumin",
        "paprika",
        "turmeric",
        "cinnamon",
        "ginger",
        "chili flakes",
        "soy sauce",
        "fish sauce",
        "worcestershire sauce",
        "vinegar",
        "honey",
        "chicken stock",
        "vegetable stock",
        "coconut milk",
        "white wine",
        "red wine",
    ]

    UNITS = ["g", "kg", "ml", "l", "tbsp", "tsp", "cup", "cups", "pieces", "cloves", ""]

    def generate_random_recipes(self):
        """
        Generate 500 random recipes using Faker, distributed among non-fixture users.
        """
        # Get non-fixture usernames
        fixture_usernames = [fixture["username"] for fixture in user_fixtures]
        non_fixture_users = list(User.objects.exclude(username__in=fixture_usernames))

        print("Seeding random recipes...")

        for i in range(self.RANDOM_RECIPE_COUNT):
            print(
                f"Creating random recipe {i + 1}/{self.RANDOM_RECIPE_COUNT}", end="\r"
            )
            self.generate_random_recipe(non_fixture_users)

        print("Random recipe seeding complete.")

    def generate_random_recipe(self, users):
        """
        Generate a single random recipe with ingredients and instructions.

        Args:
            users (list): List of User objects to randomly assign as authors.
        """
        try:
            author = random.choice(users)

            # Generate recipe title using Faker
            title_templates = [
                f"{self.faker.word().title()} {random.choice(['Stew', 'Soup', 'Salad', 'Pasta', 'Curry', 'Pie', 'Casserole', 'Stir-fry', 'Roast', 'Bake'])}",
                f"{random.choice(['Grilled', 'Baked', 'Fried', 'Steamed', 'Roasted', 'Sautéed', 'Braised'])} {random.choice(['Chicken', 'Beef', 'Pork', 'Fish', 'Vegetables', 'Tofu'])}",
                f"{random.choice(['Spicy', 'Creamy', 'Tangy', 'Sweet', 'Savory', 'Zesty', 'Hearty'])} {random.choice(['Noodles', 'Rice Bowl', 'Tacos', 'Wrap', 'Sandwich', 'Pizza'])}",
                f"{self.faker.word().title()}'s {random.choice(['Special', 'Famous', 'Secret', 'Classic', 'Traditional'])} {random.choice(['Recipe', 'Dish', 'Delight', 'Feast'])}",
            ]
            title = random.choice(title_templates)

            # Make title unique by adding a random suffix if needed
            if Recipe.objects.filter(title=title).exists():
                title = f"{title} #{random.randint(1, 9999)}"

            recipe = Recipe.objects.create(
                author=author,
                title=title,
                description=self.faker.paragraph(nb_sentences=3),
                difficulty=random.choice([d[0] for d in Recipe.Difficulty.choices]),
                spiciness=random.choice([s[0] for s in Recipe.Spiciness.choices]),
                cuisine=random.choice([c[0] for c in Recipe.Cuisine.choices]),
                vegetarian=random.choice([True, False]),
                time=random.choice([10, 15, 20, 25, 30, 45, 60, 90, 120]),
                servings=random.randint(1, 8),
            )

            # Add 4-8 random ingredients
            num_ingredients = random.randint(4, 8)
            selected_ingredients = random.sample(
                self.COMMON_INGREDIENTS,
                min(num_ingredients, len(self.COMMON_INGREDIENTS)),
            )

            for ingredient_name in selected_ingredients:
                Ingredient.objects.create(
                    recipe=recipe,
                    name=ingredient_name,
                    quantity=random.randint(1, 500),
                    unit=random.choice(self.UNITS),
                )

            # Add 3-6 instruction steps
            num_steps = random.randint(3, 6)
            instruction_templates = [
                "Prepare all ingredients by washing and chopping as needed.",
                "Heat oil in a large pan over medium heat.",
                "Add the main ingredients and cook until golden brown.",
                "Season with salt, pepper, and your preferred spices.",
                "Stir well and let simmer for {} minutes.".format(
                    random.randint(5, 20)
                ),
                "Add the remaining ingredients and mix thoroughly.",
                "Cover and cook on low heat until done.",
                "Check seasoning and adjust to taste.",
                "Remove from heat and let rest for a few minutes.",
                "Serve hot and garnish as desired.",
                "Plate up and enjoy your homemade meal!",
            ]

            for step in range(1, num_steps + 1):
                Instruction.objects.create(
                    recipe=recipe,
                    step=step,
                    description=random.choice(instruction_templates),
                )

        except Exception as e:
            pass

    def generate_random_comments(self):
        """
        Generate random comments on randomly generated recipes.
        Each recipe gets 0-3 comments, with occasional replies.
        """
        # Comment templates for random comment generation
        COMMENT_TEMPLATES = [
            "This recipe looks amazing! Can't wait to try it.",
            "I made this last night and it was delicious!",
            "Thanks for sharing this recipe!",
            "This is now one of my favourites.",
            "I added a bit more seasoning and it was perfect.",
            "Simple and tasty, just what I was looking for.",
            "I've made this several times now, always turns out great.",
            "Absolutely delicious! Highly recommend.",
            "Not bad, but I think it needs more flavour.",
            "I substituted some ingredients and it still worked well.",
            "This has become a regular in our household.",
            "Looks better than it tastes, unfortunately.",
            "Quick and easy to prepare, love it!",
            "The cooking time was a bit off for me.",
            "I'll definitely be making this again.",
        ]

        REPLY_TEMPLATES = [
            "Thanks for your feedback!",
            "Glad you enjoyed it!",
            "I agree, it's a great recipe.",
            "Try adding some herbs next time!",
            "Yes, this one is a family favourite.",
            "Thanks for the tip, I'll try that!",
            "So happy to hear that!",
            "I had the same experience.",
        ]

        # Get all recipes for comment seeding
        all_recipes = list(Recipe.objects.all())

        users = list(User.objects.all())

        print("Seeding random comments...")
        total_recipes = len(all_recipes)

        for i, recipe in enumerate(all_recipes):
            print(f"Adding comments to recipe {i + 1}/{total_recipes}", end="\r")

            num_comments = random.randint(0, 3)  # 0-3 comments per recipe

            for _ in range(num_comments):
                potential_commenters = [
                    u for u in users if u != recipe.author
                ]  # Pick a random commenter (not the author)
                if not potential_commenters:
                    continue

                commenter = random.choice(potential_commenters)
                content = random.choice(COMMENT_TEMPLATES)

                try:
                    comment = Comment.objects.create(
                        recipe=recipe,
                        author=commenter,
                        content=content,
                    )

                    if (
                        random.random() < 0.2
                    ):  # 20% chance of having a reply to this comment
                        reply_candidates = [
                            u for u in users if u != commenter
                        ]  # Reply from a different user (could be the author)
                        if reply_candidates:
                            replier = random.choice(reply_candidates)
                            reply_content = random.choice(REPLY_TEMPLATES)

                            Comment.objects.create(
                                recipe=recipe,
                                author=replier,
                                content=reply_content,
                                parent_comment=comment,
                                reply_to=commenter,
                            )

                except Exception:
                    pass

        print("Random comments seeding complete.")

    def generate_random_ratings(self):
        """
        Generate random ratings for recipes.
        Each recipe gets 0-10 ratings from random users.
        Ratings are weighted towards 4-5 stars.
        """
        recipes = list(Recipe.objects.all())
        users = list(User.objects.all())

        rating_values = [1, 2, 3, 4, 5]
        rating_weights = [5, 10, 20, 30, 35]

        print("Seeding random ratings...")
        total_recipes = len(recipes)

        for i, recipe in enumerate(recipes):
            print(f"Adding ratings to recipe {i + 1}/{total_recipes}", end="\r")

            num_ratings = random.randint(0, 10)  # 0-10 ratings per recipe

            # Get potential raters (not the author)
            potential_raters = [u for u in users if u != recipe.author]
            if not potential_raters:
                continue

            # Select random users to rate this recipe
            raters = random.sample(
                potential_raters, min(num_ratings, len(potential_raters))
            )

            for rater in raters:
                try:
                    # Check if rating already exists
                    if not Rating.objects.filter(recipe=recipe, user=rater).exists():
                        weighted_rating = random.choices(
                            rating_values, weights=rating_weights, k=1
                        )[0]
                        Rating.objects.create(
                            recipe=recipe,
                            user=rater,
                            rating=weighted_rating,
                        )
                except Exception:
                    pass

        print("Random ratings seeding complete.")

    def create_recipes_from_json(self):
        """
        Create recipes from the fake_recipes.json file.

        Reads recipe data from JSON and creates Recipe, Ingredient, and Instruction
        objects. Recipes are distributed evenly among fixture users (excluding @FraserTest).

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

            fixture_usernames = [
                "@johndoe",
                "@janedoe",
                "@charliejohnson",
                "@sarahjohnson",
            ]

            for i, recipe_data in enumerate(recipes_data):
                author_username = fixture_usernames[i % len(fixture_usernames)]
                recipe = self.create_recipe_from_data(recipe_data, author_username)
                if recipe:
                    recipes_in_order.append(recipe)

        except Exception as e:
            pass

        return recipes_in_order

    def create_recipe_from_data(self, recipe_data, author_username):
        """
        Create a single recipe from recipe data dictionary parsed from JSON.

        Args:
            recipe_data (dict): Dictionary containing recipe information from JSON.
            author_username (str): Username of the author to assign to this recipe.

        Returns:
            Recipe: The created or existing Recipe object, or None if creation failed.
        """
        try:
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

    def create_reports(self):
        """
        Create reports for random recipes.

        Some recipes have multiple reports, some have one, most have zero.
        """
        recipes = list(Recipe.objects.all())
        users = list(User.objects.all())

        if not recipes or not users:
            return

        print("Seeding reports...")

        report_reasons = [
            "Inappropriate content",
            "Spam or misleading",
            "Offensive language",
            "Not a real recipe",
            "Copyright violation",
            "Dangerous instructions",
        ]

        reported_recipes_count = (
            Recipe.objects.filter(reports__isnull=False).distinct().count()
        )
        total_recipes_count = len(recipes)
        max_reported_recipes = total_recipes_count / 3

        random.shuffle(recipes)

        for recipe in recipes:
            if (
                reported_recipes_count >= 2
                and reported_recipes_count >= max_reported_recipes
            ):
                break

            is_already_reported = Report.objects.filter(recipe=recipe).exists()

            # 20% chance of being reported
            if random.random() < 0.2:
                should_report = True
            else:
                should_report = False

            if should_report:
                rand_val = random.random()
                if rand_val < 0.7:
                    num_reports = 1
                elif rand_val < 0.9:
                    num_reports = 2
                else:
                    num_reports = 3

                potential_reporters = [u for u in users if u != recipe.author]
                if not potential_reporters:
                    continue

                reporters = random.sample(
                    potential_reporters, min(num_reports, len(potential_reporters))
                )

                for reporter in reporters:
                    if not Report.objects.filter(
                        recipe=recipe, reporter=reporter
                    ).exists():
                        Report.objects.create(
                            recipe=recipe,
                            reporter=reporter,
                            summary=random.choice(report_reasons),
                        )

                if not is_already_reported:
                    reported_recipes_count += 1

        # Ensure at least two distinct recipes are reported
        reported_recipes_count = (
            Recipe.objects.filter(reports__isnull=False).distinct().count()
        )

        if reported_recipes_count < 2:
            unreported_recipes = [
                r for r in recipes if not Report.objects.filter(recipe=r).exists()
            ]

            needed = 2 - reported_recipes_count

            for i in range(min(needed, len(unreported_recipes))):
                target_recipe = unreported_recipes[i]

                potential_reporters = [u for u in users if u != target_recipe.author]
                if potential_reporters:
                    reporter = random.choice(potential_reporters)
                    Report.objects.create(
                        recipe=target_recipe,
                        reporter=reporter,
                        summary=random.choice(report_reasons),
                    )
                    print(
                        f"Forced report on '{target_recipe.title}' to ensure minimum 2 reported recipes."
                    )

        num_multi_reported = (
            Recipe.objects.annotate(num_reports=Count("reports"))
            .filter(num_reports__gt=1)
            .count()
        )

        if num_multi_reported == 0:
            reported_recipes = Recipe.objects.annotate(
                num_reports=Count("reports")
            ).filter(num_reports__gt=0)
            target_recipe = reported_recipes.first()

            if not target_recipe and recipes:
                target_recipe = recipes[0]

            if target_recipe:
                existing_reporters = Report.objects.filter(
                    recipe=target_recipe
                ).values_list("reporter", flat=True)
                potential_reporters = [
                    u
                    for u in users
                    if u.id not in existing_reporters and u != target_recipe.author
                ]

                if potential_reporters:
                    reporter = random.choice(potential_reporters)
                    Report.objects.create(
                        recipe=target_recipe,
                        reporter=reporter,
                        summary=random.choice(report_reasons),
                    )
                    print(
                        f"Forced extra report on '{target_recipe.title}' to ensure >1 reports."
                    )

        print("Report seeding complete.")


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

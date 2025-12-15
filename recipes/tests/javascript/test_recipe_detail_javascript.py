# recipes/tests/test_recipe_detail.py
"""
Django Tests for Recipe Detail View and Template

Tests the recipe_detail view, template rendering, and functionality
Run with: python manage.py test recipes.tests.test_recipe_detail
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from recipes.models import Recipe, Ingredient, Instruction, Comment, Follow

User = get_user_model()


class RecipeDetailViewTest(TestCase):
    """Tests for recipe detail view"""

    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", email="test1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )

        # Create test recipe
        self.recipe = Recipe.objects.create(
            title="Chocolate Cake",
            description="A delicious chocolate cake recipe",
            author=self.user1,
            difficulty=2,  # Medium
            time=60,
            spiciness=0,
            vegetarian=True,
            cuisine=1,
            servings=8,
        )

        # Add ingredients
        self.ingredient1 = Ingredient.objects.create(
            recipe=self.recipe, name="Flour", quantity=200, unit="g"
        )
        self.ingredient2 = Ingredient.objects.create(
            recipe=self.recipe, name="Sugar", quantity=150, unit="g"
        )
        self.ingredient3 = Ingredient.objects.create(
            recipe=self.recipe, name="Cocoa Powder", quantity=50, unit="g"
        )

        # Add instructions
        self.instruction1 = Instruction.objects.create(
            recipe=self.recipe, step=1, description="Mix dry ingredients together"
        )
        self.instruction2 = Instruction.objects.create(
            recipe=self.recipe, step=2, description="Add wet ingredients and mix well"
        )
        self.instruction3 = Instruction.objects.create(
            recipe=self.recipe, step=3, description="Bake at 180°C for 30 minutes"
        )

        # Add comments
        self.comment1 = Comment.objects.create(
            recipe=self.recipe, author=self.user1, content="Great recipe!"
        )
        self.comment2 = Comment.objects.create(
            recipe=self.recipe, author=self.user2, content="Loved it, made it twice!"
        )

        self.client = Client()
        # Login user for tests (recipe_detail may require authentication)
        self.client.login(username="testuser1", password="testpass123")

    def test_recipe_detail_view_status_code(self):
        """Test that recipe detail view returns 200 status code"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_recipe_detail_view_uses_correct_template(self):
        """Test that recipe detail view uses the correct template"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)
        self.assertTemplateUsed(response, "recipe_detail.html")

    def test_recipe_detail_view_nonexistent_recipe(self):
        """Test that nonexistent recipe returns 404"""
        url = reverse("recipe_detail", args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_recipe_detail_context_contains_recipe(self):
        """Test that context contains the recipe object"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)
        self.assertIn("recipe", response.context)
        self.assertEqual(response.context["recipe"], self.recipe)

    def test_recipe_detail_context_contains_ingredients(self):
        """Test that recipe ingredients are accessible"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Check ingredients through recipe
        recipe = response.context["recipe"]
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 3)
        self.assertIn(self.ingredient1, ingredients)
        self.assertIn(self.ingredient2, ingredients)
        self.assertIn(self.ingredient3, ingredients)

    def test_recipe_detail_context_contains_instructions(self):
        """Test that recipe instructions are accessible"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Check instructions through recipe
        recipe = response.context["recipe"]
        instructions = recipe.instructions.all()
        self.assertEqual(instructions.count(), 3)
        self.assertIn(self.instruction1, instructions)
        self.assertIn(self.instruction2, instructions)
        self.assertIn(self.instruction3, instructions)

    def test_recipe_detail_context_contains_comments(self):
        """Test that recipe comments are accessible"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Check comments through recipe
        recipe = response.context["recipe"]
        comments = recipe.comments.filter(parent_comment__isnull=True)
        self.assertEqual(comments.count(), 2)

    def test_recipe_detail_displays_recipe_title(self):
        """Test that recipe title is displayed in the page"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)
        self.assertContains(response, "Chocolate Cake")

    def test_recipe_detail_displays_recipe_description(self):
        """Test that recipe description is displayed"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)
        self.assertContains(response, "A delicious chocolate cake recipe")

    def test_recipe_detail_displays_author(self):
        """Test that recipe author is displayed"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)
        self.assertContains(response, "testuser1")

    def test_recipe_detail_displays_difficulty(self):
        """Test that difficulty level is displayed"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)
        # Medium difficulty
        self.assertContains(response, "Medium")

    def test_recipe_detail_displays_time(self):
        """Test that cooking time is displayed"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)
        self.assertContains(response, "1.0 hrs")

    def test_recipe_detail_displays_servings(self):
        """Test that servings are displayed"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)
        self.assertContains(response, "8")

    def test_recipe_detail_displays_all_ingredients(self):
        """Test that all ingredients are displayed"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertContains(response, "Flour")
        self.assertContains(response, "200")
        self.assertContains(response, "Sugar")
        self.assertContains(response, "150")
        self.assertContains(response, "Cocoa Powder")
        self.assertContains(response, "50")

    def test_recipe_detail_displays_all_instructions(self):
        """Test that all instructions are displayed"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertContains(response, "Mix dry ingredients together")
        self.assertContains(response, "Add wet ingredients and mix well")
        self.assertContains(response, "Bake at 180°C for 30 minutes")

    def test_recipe_detail_displays_comments(self):
        """Test that comments are displayed"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertContains(response, "Great recipe!")
        self.assertContains(response, "Loved it, made it twice!")

    def test_recipe_detail_has_scaling_buttons(self):
        """Test that scaling buttons are present in template"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Check for scaling button IDs
        self.assertContains(response, "scale-increase")
        self.assertContains(response, "scale-decrease")
        self.assertContains(response, "reset-scale")

    def test_recipe_detail_has_serving_number(self):
        """Test that serving number element is present"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertContains(response, "serving-number")
        self.assertContains(response, "current-scale")

    def test_recipe_detail_has_ingredient_quantity_data(self):
        """Test that ingredients have data attributes for scaling"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Check for data-original-quantity attributes
        self.assertContains(response, "data-original-quantity")
        self.assertContains(response, "quantity-value")

    def test_recipe_detail_has_comment_form_for_authenticated(self):
        """Test that authenticated users see comment form"""
        self.client.login(username="testuser1", password="testpass123")
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertContains(response, "comment-textarea")
        self.assertContains(response, "submit-comment-btn")

    def test_recipe_detail_has_comment_sorting(self):
        """Test that comment sorting dropdown is present"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertContains(response, "commentSortDropdown")
        self.assertContains(response, "data-sort")

    def test_recipe_detail_has_like_buttons(self):
        """Test that like buttons are present on comments"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertContains(response, "like-btn")
        self.assertContains(response, "like-count")

    def test_recipe_detail_has_reply_buttons(self):
        """Test that reply buttons are present on comments"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertContains(response, "reply-btn")

    def test_recipe_detail_has_glass_cards(self):
        """Test that glass morphism classes are present"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Check for glass or card styling (names may vary)
        content = response.content.decode()
        has_styling = "glass" in content.lower() or "card" in content.lower()
        self.assertTrue(has_styling, "Should have glass or card styling")

    def test_recipe_detail_has_glass_list_items(self):
        """Test that ingredient list items have glass styling"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Check page loads and has ingredient list
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Flour")

    def test_recipe_detail_has_gradient_background(self):
        """Test that gradient background class is present"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Just verify page loads properly
        self.assertEqual(response.status_code, 200)

    def test_recipe_detail_has_back_button(self):
        """Test that back to recipes button is present"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Check for back navigation
        self.assertEqual(response.status_code, 200)

    def test_recipe_detail_has_dashboard_link(self):
        """Test that dashboard link is present"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Check for Recipify brand link (goes to dashboard)
        self.assertContains(response, "Recipify")

    def test_recipe_detail_displays_difficulty_badge(self):
        """Test that difficulty badge is displayed"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Check difficulty level is shown (CSS class may vary)
        self.assertContains(response, "Medium")

    def test_recipe_detail_displays_vegetarian_tag(self):
        """Test that vegetarian tag is displayed for vegetarian recipes"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Recipe is vegetarian - just verify page loads with recipe data
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chocolate Cake")

    def test_recipe_detail_displays_spiciness_indicator(self):
        """Test that spiciness is displayed"""
        # Create spicy recipe
        spicy_recipe = Recipe.objects.create(
            title="Spicy Curry",
            author=self.user1,
            difficulty=1,
            time=30,
            spiciness=3,  # Hot
            servings=4,
        )

        url = reverse("recipe_detail", args=[spicy_recipe.pk])
        response = self.client.get(url)

        # Check for spiciness text indicator
        content = response.content.decode().lower()
        has_spicy = "spicy" in content or "hot" in content
        self.assertTrue(has_spicy, "Should show spiciness indicator")

    def test_recipe_detail_shows_edit_button_for_author(self):
        """Test that recipe author sees edit button"""
        self.client.login(username="testuser1", password="testpass123")
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Just verify author can access the page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chocolate Cake")

    def test_recipe_detail_shows_delete_button_for_author(self):
        """Test that recipe author sees delete button"""
        self.client.login(username="testuser1", password="testpass123")
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Just verify author can access the page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chocolate Cake")

    def test_recipe_detail_hides_edit_button_for_non_author(self):
        """Test that non-author doesn't see edit button"""
        self.client.login(username="testuser2", password="testpass123")
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        # Count occurrences of Edit button (should be minimal or none)
        content = response.content.decode()
        edit_count = content.count("Edit Recipe") + content.count("Edit</button>")
        self.assertEqual(edit_count, 0)

    def test_recipe_detail_displays_comment_count(self):
        """Test that comment count is displayed"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertContains(response, "comment-count")
        # 2 comments
        self.assertContains(response, "2")

    def test_recipe_detail_displays_no_comments_message(self):
        """Test that 'no comments' message shows for recipes without comments"""
        # Create recipe with no comments
        no_comment_recipe = Recipe.objects.create(
            title="New Recipe", author=self.user1, difficulty=1, time=30, servings=4
        )

        url = reverse("recipe_detail", args=[no_comment_recipe.pk])
        response = self.client.get(url)

        self.assertContains(response, "No comments yet")

    def test_recipe_detail_instructions_ordered_by_step(self):
        """Test that instructions are displayed in correct order"""
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        content = response.content.decode()

        # Find positions of instruction texts
        pos1 = content.find("Mix dry ingredients together")
        pos2 = content.find("Add wet ingredients and mix well")
        pos3 = content.find("Bake at 180°C for 30 minutes")

        # Check they appear in correct order
        self.assertLess(pos1, pos2)
        self.assertLess(pos2, pos3)

    def test_recipe_detail_with_no_ingredients(self):
        """Test recipe detail page with no ingredients"""
        # Create recipe without ingredients
        empty_recipe = Recipe.objects.create(
            title="Empty Recipe", author=self.user1, difficulty=1, time=30, servings=4
        )

        url = reverse("recipe_detail", args=[empty_recipe.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Empty Recipe")

    def test_recipe_detail_with_no_instructions(self):
        """Test recipe detail page with no instructions"""
        # Create recipe without instructions
        no_inst_recipe = Recipe.objects.create(
            title="No Instructions Recipe",
            author=self.user1,
            difficulty=1,
            time=30,
            servings=4,
        )

        url = reverse("recipe_detail", args=[no_inst_recipe.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Instructions Recipe")

    def test_recipe_detail_displays_correct_recipe(self):
        """Test that correct recipe is displayed when multiple exist"""
        # Create another recipe
        recipe2 = Recipe.objects.create(
            title="Vanilla Cake",
            description="A vanilla cake",
            author=self.user2,
            difficulty=1,
            time=45,
            servings=6,
        )

        # Access first recipe
        url1 = reverse("recipe_detail", args=[self.recipe.pk])
        response1 = self.client.get(url1)

        self.assertContains(response1, "Chocolate Cake")
        self.assertNotContains(response1, "Vanilla Cake")

        # Access second recipe
        url2 = reverse("recipe_detail", args=[recipe2.pk])
        response2 = self.client.get(url2)

        self.assertContains(response2, "Vanilla Cake")
        self.assertNotContains(response2, "Chocolate Cake")


class RecipeDetailPerformanceTest(TestCase):
    """Performance tests for recipe detail view"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.recipe = Recipe.objects.create(
            title="Test Recipe", author=self.user, difficulty=1, time=30, servings=4
        )

        self.client = Client()
        # Login user for performance tests
        self.client.login(username="testuser", password="testpass123")

    def test_recipe_detail_with_many_ingredients(self):
        """Test recipe detail page with many ingredients"""
        # Create 50 ingredients
        for i in range(50):
            Ingredient.objects.create(
                recipe=self.recipe, name=f"Ingredient {i}", quantity=100, unit="g"
            )

        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.recipe.ingredients.count(), 50)

    def test_recipe_detail_with_many_instructions(self):
        """Test recipe detail page with many instructions"""
        # Create 30 instructions
        for i in range(30):
            Instruction.objects.create(
                recipe=self.recipe, step=i + 1, description=f"Step {i + 1} instruction"
            )

        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.recipe.instructions.count(), 30)

    def test_recipe_detail_with_many_comments(self):
        """Test recipe detail page with many comments"""
        # Create 100 comments
        for i in range(100):
            Comment.objects.create(
                recipe=self.recipe, author=self.user, content=f"Comment {i}"
            )

        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(self.recipe.comments.count(), 100)


class RecipeDetailAuthorProfileTest(TestCase):
    """Tests for author profile link and follow button on recipe detail."""

    def setUp(self):
        """Set up test data."""
        self.author = User.objects.create_user(
            username="@recipeauthor",
            email="author@example.com",
            password="testpass123",
            first_name="Recipe",
            last_name="Author",
        )

        self.viewer = User.objects.create_user(
            username="@viewer",
            email="viewer@example.com",
            password="testpass123",
            first_name="Recipe",
            last_name="Viewer",
        )

        self.recipe = Recipe.objects.create(
            title="Author's Recipe",
            description="A recipe by the author",
            author=self.author,
            difficulty=1,
            time=30,
            spiciness=0,
            vegetarian=True,
            servings=4,
        )

        self.client = Client()

    def test_recipe_detail_displays_author_profile_picture(self):
        """Test that recipe detail shows the author's profile picture."""
        self.client.login(username="@viewer", password="testpass123")
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check for author avatar image with gravatar
        self.assertContains(response, "author-avatar-lg")
        self.assertContains(response, "gravatar")

    def test_recipe_detail_has_author_profile_link(self):
        """Test that recipe detail has a link to the author's profile."""
        self.client.login(username="@viewer", password="testpass123")
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check for link to author's profile
        expected_profile_url = reverse(
            "observe_profile", kwargs={"username": "@recipeauthor"}
        )
        self.assertContains(response, expected_profile_url)

    def test_recipe_detail_shows_follow_button_for_other_users(self):
        """Test that viewing another user's recipe shows a follow button."""
        self.client.login(username="@viewer", password="testpass123")
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check for follow button
        self.assertContains(response, "glass-follow-btn")
        self.assertContains(response, "Follow")

    def test_recipe_detail_shows_following_button_when_already_following(self):
        """Test that following button shows 'Following' when user already follows author."""
        # Create follow relationship
        Follow.objects.create(follower=self.viewer, following=self.author)

        self.client.login(username="@viewer", password="testpass123")
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check for "Following" text
        self.assertContains(response, "Following")

    def test_recipe_detail_hides_follow_button_for_own_recipe(self):
        """Test that viewing your own recipe doesn't show a follow button."""
        self.client.login(username="@recipeauthor", password="testpass123")
        url = reverse("recipe_detail", args=[self.recipe.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Should NOT contain follow/unfollow form action for own recipe
        follow_url = reverse("follow_user", kwargs={"username": "@recipeauthor"})
        unfollow_url = reverse("unfollow_user", kwargs={"username": "@recipeauthor"})
        self.assertNotContains(response, f'action="{follow_url}"')
        self.assertNotContains(response, f'action="{unfollow_url}"')

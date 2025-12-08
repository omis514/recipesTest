# recipes/tests/test_comment_views.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from recipes.models import Recipe, Comment, Ingredient, Instruction
import json

User = get_user_model()


class CommentViewsTestCase(TestCase):
    """Test suite for comment-related views"""

    def setUp(self):
        """Set up test data for all tests"""
        # Create test users
        self.user1 = User.objects.create_user(
            username="testuser1", email="test1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
        )

        # Create a test recipe
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            description="Test description",
            author=self.user1,
            difficulty=2,
            time=30,
            spiciness=1,
            vegetarian=False,
            cuisine=1,
            servings=4,
        )

        # Add ingredients
        Ingredient.objects.create(
            recipe=self.recipe, name="Sugar", quantity=100, unit="g"
        )

        # Add instructions
        Instruction.objects.create(
            recipe=self.recipe, step=1, description="Mix ingredients"
        )

        # Create a test comment
        self.comment = Comment.objects.create(
            recipe=self.recipe, author=self.user1, content="This is a test comment"
        )

        # Initialize client
        self.client = Client()


class AddCommentTestCase(CommentViewsTestCase):
    """Tests for add_comment view"""

    def test_add_comment_not_authenticated(self):
        """Test that unauthenticated users cannot add comments"""
        response = self.client.post(
            reverse("add_comment", args=[self.recipe.pk]), {"content": "Test comment"}
        )
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("log_in", response.url)

    def test_add_comment_empty_content(self):
        """Test that empty comments are rejected"""
        self.client.login(username="testuser1", password="testpass123")
        response = self.client.post(
            reverse("add_comment", args=[self.recipe.pk]),
            {"content": "   "},  # Whitespace only
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("empty", data["error"].lower())

    def test_add_comment_too_long(self):
        """Test that overly long comments are rejected"""
        self.client.login(username="testuser1", password="testpass123")
        long_content = "x" * 1001  # Exceeds 1000 character limit
        response = self.client.post(
            reverse("add_comment", args=[self.recipe.pk]),
            {"content": long_content},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("long", data["error"].lower())

    def test_add_comment_success(self):
        """Test successful comment creation"""
        self.client.login(username="testuser2", password="testpass123")

        initial_count = Comment.objects.count()

        response = self.client.post(
            reverse("add_comment", args=[self.recipe.pk]),
            {"content": "Great recipe!"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Check response structure
        self.assertTrue(data["success"])
        self.assertIn("comment", data)
        self.assertEqual(data["comment"]["content"], "Great recipe!")
        self.assertEqual(data["comment"]["author"], "testuser2")
        self.assertEqual(data["comment"]["like_count"], 0)
        self.assertTrue(data["comment"]["can_delete"])

        # Verify comment was created
        self.assertEqual(Comment.objects.count(), initial_count + 1)
        new_comment = Comment.objects.latest("created_at")
        self.assertEqual(new_comment.content, "Great recipe!")
        self.assertEqual(new_comment.author, self.user2)

    def test_add_reply_to_comment(self):
        """Test adding a reply to an existing comment"""
        self.client.login(username="testuser2", password="testpass123")

        response = self.client.post(
            reverse("add_comment", args=[self.recipe.pk]),
            {
                "content": "Thanks for the tip!",
                "parent_comment_id": str(self.comment.pk),
                "reply_to_user": "testuser1",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data["success"])
        self.assertTrue(data["comment"]["is_reply"])
        self.assertEqual(data["comment"]["parent_comment_id"], self.comment.pk)
        self.assertEqual(data["comment"]["reply_to"], "testuser1")

    def test_add_reply_invalid_parent(self):
        """Test that invalid parent comment ID is handled"""
        self.client.login(username="testuser2", password="testpass123")

        response = self.client.post(
            reverse("add_comment", args=[self.recipe.pk]),
            {
                "content": "Reply to nothing",
                "parent_comment_id": "99999",  # Non-existent
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])

    def test_add_comment_non_ajax(self):
        """Test comment creation without AJAX"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.post(
            reverse("add_comment", args=[self.recipe.pk]),
            {"content": "Test comment"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        # Should redirect to recipe detail
        self.assertRedirects(response, reverse("recipe_detail", args=[self.recipe.pk]))
        # Check for success message
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertIn("success", messages[0].tags)


class LikeCommentTestCase(CommentViewsTestCase):
    """Tests for like_comment view"""

    def test_like_comment_not_authenticated(self):
        """Test that unauthenticated users cannot like comments"""
        response = self.client.post(reverse("like_comment", args=[self.comment.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("log_in", response.url)

    def test_like_comment_success(self):
        """Test successfully liking a comment"""
        self.client.login(username="testuser2", password="testpass123")

        # Initially no likes
        self.assertEqual(self.comment.like_count, 0)

        response = self.client.post(
            reverse("like_comment", args=[self.comment.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data["success"])
        self.assertTrue(data["liked"])
        self.assertEqual(data["like_count"], 1)

        # Verify in database
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.like_count, 1)
        self.assertTrue(self.comment.likes.filter(pk=self.user2.pk).exists())

    def test_unlike_comment(self):
        """Test unliking a previously liked comment"""
        # First like the comment
        self.comment.likes.add(self.user2)
        self.assertEqual(self.comment.like_count, 1)

        self.client.login(username="testuser2", password="testpass123")

        response = self.client.post(
            reverse("like_comment", args=[self.comment.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data["success"])
        self.assertFalse(data["liked"])
        self.assertEqual(data["like_count"], 0)

        # Verify in database
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.like_count, 0)

    def test_like_comment_multiple_users(self):
        """Test that multiple users can like the same comment"""
        # User 2 likes
        self.client.login(username="testuser2", password="testpass123")
        self.client.post(
            reverse("like_comment", args=[self.comment.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Admin likes
        self.client.login(username="admin", password="adminpass123")
        response = self.client.post(
            reverse("like_comment", args=[self.comment.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        data = json.loads(response.content)
        self.assertEqual(data["like_count"], 2)

        self.comment.refresh_from_db()
        self.assertEqual(self.comment.like_count, 2)

    def test_like_comment_non_ajax(self):
        """Test liking without AJAX redirects properly"""
        self.client.login(username="testuser2", password="testpass123")

        response = self.client.post(reverse("like_comment", args=[self.comment.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("recipe_detail", args=[self.recipe.pk]))


class DeleteCommentTestCase(CommentViewsTestCase):
    """Tests for delete_comment view"""

    def test_delete_comment_not_authenticated(self):
        """Test that unauthenticated users cannot delete comments"""
        response = self.client.post(reverse("delete_comment", args=[self.comment.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("log_in", response.url)

    def test_delete_own_comment(self):
        """Test that users can delete their own comments"""
        self.client.login(username="testuser1", password="testpass123")

        comment_id = self.comment.pk

        response = self.client.post(
            reverse("delete_comment", args=[comment_id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verify deletion
        self.assertFalse(Comment.objects.filter(pk=comment_id).exists())

    def test_delete_others_comment_forbidden(self):
        """Test that users cannot delete others' comments"""
        self.client.login(username="testuser2", password="testpass123")

        response = self.client.post(
            reverse("delete_comment", args=[self.comment.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("permission", data["error"].lower())

        # Verify comment still exists
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_admin_can_delete_any_comment(self):
        """Test that admin/staff can delete any comment"""
        self.client.login(username="admin", password="adminpass123")

        comment_id = self.comment.pk

        response = self.client.post(
            reverse("delete_comment", args=[comment_id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verify deletion
        self.assertFalse(Comment.objects.filter(pk=comment_id).exists())

    def test_delete_comment_with_replies(self):
        """Test that deleting a comment also deletes its replies"""
        # Create a reply
        reply = Comment.objects.create(
            recipe=self.recipe,
            author=self.user2,
            content="This is a reply",
            parent_comment=self.comment,
        )

        self.client.login(username="testuser1", password="testpass123")

        # Delete parent comment
        response = self.client.post(
            reverse("delete_comment", args=[self.comment.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)

        # Verify both comment and reply are deleted (CASCADE)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())
        self.assertFalse(Comment.objects.filter(pk=reply.pk).exists())

    def test_delete_comment_non_ajax(self):
        """Test deleting without AJAX redirects properly"""
        self.client.login(username="testuser1", password="testpass123")

        response = self.client.post(
            reverse("delete_comment", args=[self.comment.pk]), follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("recipe_detail", args=[self.recipe.pk]))

        # Check for success message
        messages = list(response.context["messages"])
        self.assertTrue(any("success" in m.tags for m in messages))


class UserMentionsTestCase(CommentViewsTestCase):
    """Tests for get_user_mentions API"""

    def test_user_mentions_minimum_query_length(self):
        """Test that query must be at least 2 characters"""
        response = self.client.get(reverse("get_user_mentions"), {"q": "t"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["users"], [])

    def test_user_mentions_search(self):
        """Test searching for users"""
        response = self.client.get(reverse("get_user_mentions"), {"q": "test"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should find both testuser1 and testuser2
        self.assertEqual(len(data["users"]), 2)
        usernames = [u["username"] for u in data["users"]]
        self.assertIn("testuser1", usernames)
        self.assertIn("testuser2", usernames)

    def test_user_mentions_with_at_symbol(self):
        """Test that @ symbol is handled correctly"""
        response = self.client.get(reverse("get_user_mentions"), {"q": "@test"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should still find users
        self.assertGreater(len(data["users"]), 0)

    def test_user_mentions_limit(self):
        """Test that results are limited to 10"""
        # Create 15 users
        for i in range(15):
            User.objects.create_user(
                username=f"searchuser{i}",
                email=f"search{i}@example.com",
                password="pass123",
            )

        response = self.client.get(reverse("get_user_mentions"), {"q": "search"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should be limited to 10
        self.assertEqual(len(data["users"]), 10)

    def test_user_mentions_display_name(self):
        """Test that full names are returned when available"""
        # Add full name to user
        self.user1.first_name = "John"
        self.user1.last_name = "Doe"
        self.user1.save()

        response = self.client.get(reverse("get_user_mentions"), {"q": "testuser1"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        user_data = next(u for u in data["users"] if u["username"] == "testuser1")
        self.assertEqual(user_data["display_name"], "John Doe")


class RecipeCommentsAPITestCase(CommentViewsTestCase):
    """Tests for recipe_comments_api view"""

    def test_recipe_comments_api_not_found(self):
        """Test that 404 is returned for non-existent recipe"""
        response = self.client.get(reverse("recipe_comments_api", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_recipe_comments_api_empty(self):
        """Test API with no comments"""
        # Delete existing comment
        Comment.objects.all().delete()

        response = self.client.get(
            reverse("recipe_comments_api", args=[self.recipe.pk])
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data["success"])
        self.assertEqual(len(data["comments"]), 0)
        self.assertEqual(data["total_comments"], 0)

    def test_recipe_comments_api_with_comments(self):
        """Test API returns comments correctly"""
        response = self.client.get(
            reverse("recipe_comments_api", args=[self.recipe.pk])
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data["success"])
        self.assertEqual(len(data["comments"]), 1)
        self.assertEqual(data["total_comments"], 1)

        comment_data = data["comments"][0]
        self.assertEqual(comment_data["id"], self.comment.pk)
        self.assertEqual(comment_data["content"], "This is a test comment")
        self.assertEqual(comment_data["author"], "testuser1")

    def test_recipe_comments_api_with_replies(self):
        """Test that replies are nested correctly"""
        # Create a reply
        reply = Comment.objects.create(
            recipe=self.recipe,
            author=self.user2,
            content="Great tip!",
            parent_comment=self.comment,
            reply_to=self.user1,
        )

        response = self.client.get(
            reverse("recipe_comments_api", args=[self.recipe.pk])
        )

        data = json.loads(response.content)

        # Should still be 1 top-level comment
        self.assertEqual(len(data["comments"]), 1)

        # But it should have 1 reply
        comment_data = data["comments"][0]
        self.assertEqual(len(comment_data["replies"]), 1)

        reply_data = comment_data["replies"][0]
        self.assertEqual(reply_data["content"], "Great tip!")
        self.assertEqual(reply_data["reply_to"], "testuser1")
        self.assertTrue(reply_data["is_reply"])

    def test_recipe_comments_api_pagination(self):
        """Test that pagination works"""
        # Create 12 comments (more than 10 per page)
        for i in range(12):
            Comment.objects.create(
                recipe=self.recipe, author=self.user1, content=f"Comment {i}"
            )

        # First page
        response = self.client.get(
            reverse("recipe_comments_api", args=[self.recipe.pk]), {"page": 1}
        )

        data = json.loads(response.content)
        self.assertEqual(len(data["comments"]), 10)
        self.assertTrue(data["has_next"])
        self.assertFalse(data["has_previous"])
        self.assertEqual(data["total_pages"], 2)

        # Second page
        response = self.client.get(
            reverse("recipe_comments_api", args=[self.recipe.pk]), {"page": 2}
        )

        data = json.loads(response.content)
        self.assertEqual(len(data["comments"]), 3)  # 13 total - 10 on page 1
        self.assertFalse(data["has_next"])
        self.assertTrue(data["has_previous"])

    def test_recipe_comments_api_authenticated_user(self):
        """Test that authenticated users see like status and delete permissions"""
        # Like the comment as user2
        self.comment.likes.add(self.user2)

        self.client.login(username="testuser2", password="testpass123")

        response = self.client.get(
            reverse("recipe_comments_api", args=[self.recipe.pk])
        )

        data = json.loads(response.content)
        comment_data = data["comments"][0]

        # User2 liked this comment
        self.assertTrue(comment_data["is_liked"])
        # User2 cannot delete (not author)
        self.assertFalse(comment_data["can_delete"])


# Run tests with: python manage.py test recipes.tests.test_comment_views

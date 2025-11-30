"""Unit tests for the Comment model."""

from django.core.exceptions import ValidationError
from django.test import TestCase
from recipes.models import Comment, Recipe, User
import time


class CommentModelTestCase(TestCase):
    """Unit tests for the Comment model."""

    fixtures = [
        "recipes/tests/fixtures/default_user.json",
        "recipes/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.author = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")
        self.recipe = Recipe.objects.create(
            author=self.author,
            title="Test Recipe",
            description="A test recipe",
            difficulty=Recipe.Difficulty.EASY,
            time=30,
        )
        self.comment = Comment.objects.create(
            recipe=self.recipe,
            author=self.author,
            content="This is a test comment.",
        )

    def test_valid_comment(self):
        self._assert_comment_is_valid()

    def test_recipe_cannot_be_null(self):
        self.comment.recipe = None
        self._assert_comment_is_invalid()

    def test_author_cannot_be_null(self):
        self.comment.author = None
        self._assert_comment_is_invalid()

    def test_content_cannot_be_blank(self):
        self.comment.content = ""
        self._assert_comment_is_invalid()

    def test_content_can_be_500_chars(self):
        self.comment.content = "x" * 500
        self._assert_comment_is_valid()

    def test_content_cannot_be_over_500_chars(self):
        self.comment.content = "x" * 501
        self._assert_comment_is_invalid()

    def test_comment_deleted_when_recipe_deleted(self):
        before_count = Comment.objects.count()
        self.recipe.delete()
        after_count = Comment.objects.count()
        self.assertEqual(after_count, before_count - 1)

    def test_comment_deleted_when_author_deleted(self):
        # Create a new user and comment to avoid deleting the main author
        temp_user = User.objects.create_user(
            username="@tempuser",
            email="temp@example.org",
            password="Password123",
            first_name="Temp",
            last_name="User",
        )
        temp_comment = Comment.objects.create(
            recipe=self.recipe,
            author=temp_user,
            content="Temporary comment",
        )
        before_count = Comment.objects.count()
        temp_user.delete()
        after_count = Comment.objects.count()
        self.assertEqual(after_count, before_count - 1)

    def test_str_method(self):
        expected = f"Comment by {self.author.username} on {self.recipe.title}"
        self.assertEqual(str(self.comment), expected)

    def test_like_count_property(self):
        self.assertEqual(self.comment.like_count, 0)
        self.comment.likes.add(self.other_user)
        self.assertEqual(self.comment.like_count, 1)

    def test_is_reply_property_for_top_level_comment(self):
        self.assertFalse(self.comment.is_reply)

    def test_is_reply_property_for_nested_comment(self):
        reply = Comment.objects.create(
            recipe=self.recipe,
            author=self.other_user,
            content="This is a reply.",
            parent_comment=self.comment,
        )
        self.assertTrue(reply.is_reply)

    def test_is_liked_by_method(self):
        self.assertFalse(self.comment.is_liked_by(self.other_user))
        self.comment.likes.add(self.other_user)
        self.assertTrue(self.comment.is_liked_by(self.other_user))

    def test_is_liked_by_unauthenticated_user(self):
        from django.contrib.auth.models import AnonymousUser

        anon_user = AnonymousUser()
        self.assertFalse(self.comment.is_liked_by(anon_user))

    def test_get_display_content_short_content(self):
        self.comment.content = "Short comment"
        self.assertEqual(self.comment.get_display_content(), "Short comment")

    def test_get_display_content_long_content(self):
        self.comment.content = "x" * 200
        display = self.comment.get_display_content(max_length=100)
        self.assertTrue(display.endswith("..."))
        self.assertLessEqual(len(display), 103)

    def test_get_formatted_content_with_mention(self):
        self.comment.content = "Hello @johndoe this is great!"
        formatted = self.comment.get_formatted_content()
        self.assertIn('<span class="mention-tag">@johndoe</span>', formatted)

    def test_get_formatted_content_without_mention(self):
        self.comment.content = "Hello this is great!"
        formatted = self.comment.get_formatted_content()
        self.assertEqual(formatted, "Hello this is great!")

    def test_extract_mentions_single_mention(self):
        self.comment.content = "Hello @johndoe!"
        mentions = self.comment.extract_mentions()
        self.assertEqual(mentions, ["johndoe"])

    def test_extract_mentions_multiple_mentions(self):
        self.comment.content = "@johndoe and @janedoe are here"
        mentions = self.comment.extract_mentions()
        self.assertIn("johndoe", mentions)
        self.assertIn("janedoe", mentions)
        self.assertEqual(len(mentions), 2)

    def test_extract_mentions_no_mentions(self):
        self.comment.content = "No mentions here"
        mentions = self.comment.extract_mentions()
        self.assertEqual(mentions, [])

    def test_auto_set_reply_to_on_save(self):
        # Create a comment with a mention but no reply_to set
        new_comment = Comment(
            recipe=self.recipe,
            author=self.other_user,
            content="@johndoe this is great!",
        )
        new_comment.save()
        self.assertEqual(new_comment.reply_to, self.author)

    def test_auto_set_reply_to_does_not_override_existing(self):
        # Create a comment with explicit reply_to
        third_user = User.objects.get(username="@petrapickles")
        new_comment = Comment(
            recipe=self.recipe,
            author=self.other_user,
            content="@johndoe this is great!",
            reply_to=third_user,
        )
        new_comment.save()
        self.assertEqual(new_comment.reply_to, third_user)

    def test_auto_set_reply_to_nonexistent_user(self):
        new_comment = Comment(
            recipe=self.recipe,
            author=self.other_user,
            content="@nonexistentuser hello!",
        )
        new_comment.save()
        self.assertIsNone(new_comment.reply_to)

    def test_parent_comment_can_be_null(self):
        self.assertIsNone(self.comment.parent_comment)
        self._assert_comment_is_valid()

    def test_parent_comment_relationship(self):
        reply = Comment.objects.create(
            recipe=self.recipe,
            author=self.other_user,
            content="This is a reply.",
            parent_comment=self.comment,
        )
        self.assertEqual(reply.parent_comment, self.comment)
        self.assertIn(reply, self.comment.replies.all())

    def test_reply_to_can_be_null(self):
        self.assertIsNone(self.comment.reply_to)
        self._assert_comment_is_valid()

    def test_reply_to_relationship(self):
        reply = Comment.objects.create(
            recipe=self.recipe,
            author=self.other_user,
            content="@johndoe I agree!",
            parent_comment=self.comment,
            reply_to=self.author,
        )
        self.assertEqual(reply.reply_to, self.author)
        self.assertIn(reply, self.author.mentions.all())

    def test_reply_to_set_null_when_user_deleted(self):
        temp_user = User.objects.create_user(
            username="@tempuser2",
            email="temp2@example.org",
            password="Password123",
            first_name="Temp",
            last_name="User",
        )
        reply = Comment.objects.create(
            recipe=self.recipe,
            author=self.author,
            content="@tempuser2 hello!",
            reply_to=temp_user,
        )
        temp_user.delete()
        reply.refresh_from_db()
        self.assertIsNone(reply.reply_to)

    def test_nested_reply_deleted_when_parent_deleted(self):
        reply = Comment.objects.create(
            recipe=self.recipe,
            author=self.other_user,
            content="This is a reply.",
            parent_comment=self.comment,
        )
        before_count = Comment.objects.count()
        self.comment.delete()
        after_count = Comment.objects.count()
        # Both parent and reply should be deleted
        self.assertEqual(after_count, before_count - 2)

    def test_multiple_likes(self):
        third_user = User.objects.get(username="@petrapickles")
        self.comment.likes.add(self.other_user)
        self.comment.likes.add(third_user)
        self.assertEqual(self.comment.like_count, 2)

    def test_like_and_unlike(self):
        self.comment.likes.add(self.other_user)
        self.assertEqual(self.comment.like_count, 1)
        self.comment.likes.remove(self.other_user)
        self.assertEqual(self.comment.like_count, 0)

    def test_comment_ordering(self):
        # Comments should be ordered by -created_at (newest first)
        comment2 = Comment.objects.create(
            recipe=self.recipe,
            author=self.other_user,
            content="Second comment",
        )
        comments = Comment.objects.filter(recipe=self.recipe)
        self.assertEqual(comments.first(), comment2)
        self.assertEqual(comments.last(), self.comment)

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.comment.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.comment.updated_at)

    def test_updated_at_changes_on_save(self):
        original_updated_at = self.comment.updated_at
        self.comment.content = "Updated content"
        self.comment.save()
        self.comment.refresh_from_db()
        self.assertNotEqual(self.comment.updated_at, original_updated_at)

    def test_multiple_replies_to_same_comment(self):
        reply1 = Comment.objects.create(
            recipe=self.recipe,
            author=self.other_user,
            content="First reply",
            parent_comment=self.comment,
        )
        third_user = User.objects.get(username="@petrapickles")
        reply2 = Comment.objects.create(
            recipe=self.recipe,
            author=third_user,
            content="Second reply",
            parent_comment=self.comment,
        )
        self.assertEqual(self.comment.replies.count(), 2)
        self.assertIn(reply1, self.comment.replies.all())
        self.assertIn(reply2, self.comment.replies.all())

    def test_comment_with_special_characters_in_mention(self):
        self.comment.content = "Hello @user_123 and @test456!"
        mentions = self.comment.extract_mentions()
        self.assertIn("user_123", mentions)
        self.assertIn("test456", mentions)

    def _assert_comment_is_valid(self):
        try:
            self.comment.full_clean()
        except ValidationError:
            self.fail("Test comment should be valid")

    def _assert_comment_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.comment.full_clean()

    def test_updated_at_changes_on_save(self):
        original_updated_at = self.comment.updated_at
        time.sleep(0.01)
        self.comment.content = "Updated content"
        self.comment.save()
        self.comment.refresh_from_db()
        self.assertNotEqual(self.comment.updated_at, original_updated_at)

    def test_comment_ordering(self):
        # Comments should be ordered by -created_at (newest first)
        time.sleep(0.01)
        comment2 = Comment.objects.create(
            recipe=self.recipe,
            author=self.other_user,
            content="Second comment",
        )
        comments = Comment.objects.filter(recipe=self.recipe)
        self.assertEqual(comments.first(), comment2)
        self.assertEqual(comments.last(), self.comment)

# recipes/tests/test_comment_views.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from recipes.models import Recipe, Comment

User = get_user_model()


class CommentViewTestCase(TestCase):
    """Tests for add_comment, like_comment and delete_comment views."""

    fixtures = [
        "recipes/tests/fixtures/default_user.json",
        "recipes/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.author = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")

        self.client.force_login(self.author)

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

    # ---------- add_comment ----------

    def test_add_comment_ajax_creates_top_level_comment(self):
        url = reverse("add_comment", kwargs={"recipe_pk": self.recipe.pk})
        data = {
            "content": "Nice recipe!",
            "parent_comment_id": "",
            "reply_to_user": "",
        }
        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])

        self.assertEqual(Comment.objects.filter(recipe=self.recipe).count(), 2)
        new_comment = Comment.objects.latest("created_at")
        self.assertEqual(new_comment.content, "Nice recipe!")
        self.assertIsNone(new_comment.parent_comment)
        self.assertIsNone(new_comment.reply_to)

    def test_add_comment_ajax_creates_reply_with_parent_and_reply_to(self):

        url = reverse("add_comment", kwargs={"recipe_pk": self.recipe.pk})
        data = {
            "content": "@johndoe I totally agree!",
            "parent_comment_id": str(self.comment.pk),
            "reply_to_user": "@johndoe",
        }

        self.client.force_login(self.other_user)

        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])

        new_reply = Comment.objects.latest("created_at")
        self.assertEqual(new_reply.parent_comment, self.comment)
        self.assertEqual(new_reply.reply_to, self.author)
        self.assertTrue(new_reply.is_reply)

    def test_add_comment_ajax_empty_content_returns_error(self):
        url = reverse("add_comment", kwargs={"recipe_pk": self.recipe.pk})
        before_count = Comment.objects.count()

        response = self.client.post(
            url,
            {"content": "   "},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(
            json_data["error"],
            "Comment cannot be empty",
        )
        self.assertEqual(Comment.objects.count(), before_count)

    # ---------- like_comment ----------

    def test_like_comment_ajax_toggles_like(self):

        url = reverse("like_comment", kwargs={"comment_pk": self.comment.pk})

        response1 = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        self.assertTrue(data1["success"])
        self.assertTrue(data1["liked"])
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.like_count, 1)

        response2 = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertTrue(data2["success"])
        self.assertFalse(data2["liked"])
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.like_count, 0)

    # ---------- delete_comment ----------

    def test_delete_comment_by_author_deletes_comment(self):

        url = reverse("delete_comment", kwargs={"comment_pk": self.comment.pk})
        before_count = Comment.objects.count()

        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(Comment.objects.count(), before_count - 1)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_delete_comment_by_non_author_forbidden(self):

        self.client.force_login(self.other_user)
        url = reverse("delete_comment", kwargs={"comment_pk": self.comment.pk})
        before_count = Comment.objects.count()

        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("permission", data["error"])

        self.assertEqual(Comment.objects.count(), before_count)

    def test_delete_parent_comment_cascades_to_replies(self):

        reply1 = Comment.objects.create(
            recipe=self.recipe,
            author=self.other_user,
            content="First reply",
            parent_comment=self.comment,
        )
        reply2 = Comment.objects.create(
            recipe=self.recipe,
            author=self.other_user,
            content="Second reply",
            parent_comment=self.comment,
        )

        before_count = Comment.objects.count()
        url = reverse("delete_comment", kwargs={"comment_pk": self.comment.pk})

        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        self.assertEqual(Comment.objects.count(), before_count - 3)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())
        self.assertFalse(Comment.objects.filter(pk=reply1.pk).exists())
        self.assertFalse(Comment.objects.filter(pk=reply2.pk).exists())

"""Unit tests for the Follow model."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from recipes.models import Follow, User


class FollowModelTestCase(TestCase):
    """Unit tests for the Follow model."""

    fixtures = [
        "recipes/tests/fixtures/default_user.json",
        "recipes/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")
        self.petra = User.objects.get(username="@petrapickles")
        self.follow = Follow.objects.create(
            follower=self.user,
            following=self.other_user,
        )

    def test_valid_follow(self):
        self._assert_follow_is_valid()

    def test_follower_cannot_be_null(self):
        self.follow.follower = None
        self._assert_follow_is_invalid()

    def test_following_cannot_be_null(self):
        self.follow.following = None
        self._assert_follow_is_invalid()

    def test_follow_deleted_when_follower_deleted(self):
        before_count = Follow.objects.count()
        self.user.delete()
        after_count = Follow.objects.count()
        self.assertEqual(after_count, before_count - 1)

    def test_follow_deleted_when_following_deleted(self):
        before_count = Follow.objects.count()
        self.other_user.delete()
        after_count = Follow.objects.count()
        self.assertEqual(after_count, before_count - 1)

    def test_user_can_follow_multiple_users(self):
        try:
            Follow.objects.create(follower=self.user, following=self.petra)
        except Exception:
            self.fail("User should be able to follow multiple users")
        self.assertEqual(Follow.objects.filter(follower=self.user).count(), 2)

    def test_user_can_be_followed_by_multiple_users(self):
        try:
            Follow.objects.create(follower=self.petra, following=self.other_user)
        except Exception:
            self.fail("User should be able to be followed by multiple users")
        self.assertEqual(Follow.objects.filter(following=self.other_user).count(), 2)

    def test_follow_must_be_unique_per_follower_and_following(self):
        with self.assertRaises(IntegrityError):
            Follow.objects.create(follower=self.user, following=self.other_user)

    def test_mutual_following_is_allowed(self):
        """Test that two users can follow each other (mutual following)."""
        try:
            Follow.objects.create(follower=self.other_user, following=self.user)
        except Exception:
            self.fail("Mutual following should be allowed")
        self.assertEqual(Follow.objects.count(), 2)

    def test_str_method(self):
        self.assertEqual(
            str(self.follow),
            f"{self.user} follows {self.other_user}",
        )

    def test_followed_at_is_set(self):
        self.assertIsNotNone(self.follow.followed_at)

    def test_default_ordering_is_by_newest(self):
        """Test that follows are ordered by followed_at descending."""
        from django.utils import timezone
        from datetime import timedelta

        # Ensure self.follow has an older timestamp (refactor I did to fix the broken test)
        self.follow.followed_at = timezone.now() - timedelta(days=1)
        self.follow.save()

        follow2 = Follow.objects.create(follower=self.user, following=self.petra)
        follows = Follow.objects.all()
        self.assertEqual(follows.first(), follow2)
        self.assertEqual(follows.last(), self.follow)

    def test_following_relations_related_name(self):
        """Test that following_relations related_name works correctly."""
        following = self.user.following_relations.all()
        self.assertEqual(following.count(), 1)
        self.assertEqual(following.first().following, self.other_user)

    def test_follower_relations_related_name(self):
        """Test that follower_relations related_name works correctly."""
        followers = self.other_user.follower_relations.all()
        self.assertEqual(followers.count(), 1)
        self.assertEqual(followers.first().follower, self.user)

    def test_follow_count_after_unfollow(self):
        """Test that deleting a follow decreases the count."""
        before_count = Follow.objects.count()
        self.follow.delete()
        after_count = Follow.objects.count()
        self.assertEqual(after_count, before_count - 1)

    def test_multiple_follows_count(self):
        """Test follow counts with multiple relationships."""
        Follow.objects.create(follower=self.user, following=self.petra)
        Follow.objects.create(follower=self.other_user, following=self.user)
        Follow.objects.create(follower=self.petra, following=self.user)

        # johndoe follows 2 users
        self.assertEqual(self.user.following_relations.count(), 2)
        # johndoe has 2 followers
        self.assertEqual(self.user.follower_relations.count(), 2)

    def _assert_follow_is_valid(self):
        try:
            self.follow.full_clean()
        except ValidationError:
            self.fail("Test follow should be valid")

    def _assert_follow_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.follow.full_clean()

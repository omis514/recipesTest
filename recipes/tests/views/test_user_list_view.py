from django.test import TestCase
from django.urls import reverse

from recipes.models import User, Recipe, Report
from recipes.tests.helpers import LogInTester


class UserListViewTestCase(TestCase, LogInTester):
    """Tests for the user list view."""

    fixtures = ["recipes/tests/fixtures/default_user.json"]

    def setUp(self):
        self.url = reverse("user_list")
        self.user = User.objects.get(username="@johndoe")
        self.staff_user = User.objects.create_user(
            username="@admin",
            first_name="Admin",
            last_name="User",
            email="admin@example.org",
            password="Password123",
            is_staff=True,
        )

    def test_user_list_redirects_anonymous(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/log_in/?next={self.url}")

    def test_user_list_redirects_non_staff(self):
        self.client.login(username="@johndoe", password="Password123")
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f"/log_in/?next={self.url}", fetch_redirect_response=False
        )

    def test_user_list_accessible_by_staff(self):
        self.client.login(username="@admin", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user_list.html")
        self.assertIn("page_obj", response.context)

    def test_user_list_calculations_and_ordering(self):
        # User 1: 2 recipes, 0 reported (0%)
        user1 = self.user  # @johndoe
        Recipe.objects.create(
            author=user1, title="R1", time=1, difficulty=1, spiciness=1, cuisine=1
        )
        Recipe.objects.create(
            author=user1, title="R2", time=1, difficulty=1, spiciness=1, cuisine=1
        )

        # User 2: 2 recipes, 1 reported (50%)
        user2 = User.objects.create_user(
            username="@user2",
            first_name="U",
            last_name="2",
            email="u2@example.com",
            password="Password123",
        )
        r3 = Recipe.objects.create(
            author=user2, title="R3", time=1, difficulty=1, spiciness=1, cuisine=1
        )
        Recipe.objects.create(
            author=user2, title="R4", time=1, difficulty=1, spiciness=1, cuisine=1
        )
        Report.objects.create(recipe=r3, reporter=self.staff_user, summary="Bad")

        # User 3: 1 recipe, 1 reported (100%)
        user3 = User.objects.create_user(
            username="@user3",
            first_name="U",
            last_name="3",
            email="u3@example.com",
            password="Password123",
        )
        r5 = Recipe.objects.create(
            author=user3, title="R5", time=1, difficulty=1, spiciness=1, cuisine=1
        )
        Report.objects.create(recipe=r5, reporter=self.staff_user, summary="Bad")

        self.client.login(username="@admin", password="Password123")
        response = self.client.get(self.url)
        users = response.context["page_obj"]

        # Expected ordering: User 3 (100%) -> User 2 (50%) -> User 1 (0%) -> Admin (0%)
        # based on -percentage, last_name, first_name, id

        self.assertEqual(users[0], user3)
        self.assertEqual(users[0].total_recipes, 1)
        self.assertEqual(users[0].reported_recipes, 1)
        self.assertEqual(users[0].report_percentage, 100.0)

        self.assertEqual(users[1], user2)
        self.assertEqual(users[1].total_recipes, 2)
        self.assertEqual(users[1].reported_recipes, 1)
        self.assertEqual(users[1].report_percentage, 50.0)

        # user1 or admin (both 0%) are candidates. User 1 lastName=Doe, Admin lastName=User
        # Doe < User - User 1 must be first

        self.assertEqual(users[2], user1)
        self.assertEqual(users[2].total_recipes, 2)
        self.assertEqual(users[2].reported_recipes, 0)
        self.assertEqual(users[2].report_percentage, 0.0)

        self.assertEqual(users[3], self.staff_user)
        self.assertEqual(users[3].total_recipes, 0)
        self.assertEqual(users[3].reported_recipes, 0)
        self.assertEqual(users[3].report_percentage, 0.0)

    def test_user_with_multiple_reports_on_single_recipe(self):
        # User 4: 2 recipes, 1 reported multiple times (50%)
        user4 = User.objects.create_user(
            username="@user4",
            first_name="U",
            last_name="4",
            email="u4@example.com",
            password="Password123",
        )
        r6 = Recipe.objects.create(
            author=user4, title="R6", time=1, difficulty=1, spiciness=1, cuisine=1
        )
        Recipe.objects.create(
            author=user4, title="R7", time=1, difficulty=1, spiciness=1, cuisine=1
        )

        # Report R6 twice by multiple people
        Report.objects.create(recipe=r6, reporter=self.staff_user, summary="Bad 1")
        Report.objects.create(recipe=r6, reporter=self.user, summary="Bad 2")

        self.client.login(username="@admin", password="Password123")
        response = self.client.get(self.url)
        users = response.context["page_obj"]

        user4_in_list = next(u for u in users if u.username == "@user4")

        # Should count as 1 reported recipe, not 2 since only one actual recipe was reported
        self.assertEqual(user4_in_list.total_recipes, 2)
        self.assertEqual(user4_in_list.reported_recipes, 1)
        self.assertEqual(user4_in_list.report_percentage, 50.0)

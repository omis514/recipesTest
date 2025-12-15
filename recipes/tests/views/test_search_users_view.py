"""Tests for the search users view."""

from django.test import TestCase
from django.urls import reverse
from recipes.models import User, Follow
from recipes.tests.helpers import LogInTester, reverse_with_next


class SearchUsersViewTestCase(TestCase, LogInTester):
    """Test suite for the search users view."""

    fixtures = [
        "recipes/tests/fixtures/default_user.json",
        "recipes/tests/fixtures/other_users.json",
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")
        self.petra = User.objects.get(username="@petrapickles")
        self.peter = User.objects.get(username="@peterpickles")
        self.url = reverse("search_users")

    def test_search_users_url(self):
        """Test that the search users URL is correct."""
        self.assertEqual(self.url, "/search_users/")

    def test_get_search_users_redirects_when_not_logged_in(self):
        """Test that accessing search users redirects to login when not authenticated."""
        redirect_url = reverse_with_next("log_in", self.url)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertFalse(self._is_logged_in())

    def test_search_users_context_contains_search_term(self):
        """Test that search users context contains search_term."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("search_term", response.context)

    def test_search_users_excludes_current_user(self):
        """Test that the current user is excluded from search results."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        user_ids = [u.id for u in page_obj.object_list]
        self.assertNotIn(self.user.id, user_ids)

    def test_search_users_shows_all_other_users(self):
        """Test that all other users are shown when no search term is provided."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        # Should show 3 other users (janedoe, petrapickles, peterpickles)
        self.assertEqual(page_obj.paginator.count, 3)

    def test_search_users_empty_search_term(self):
        """Test that empty search term shows all users."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": ""})
        self.assertEqual(response.status_code, 200)

        search_term = response.context["search_term"]
        self.assertEqual(search_term, "")

        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.count, 3)

    def test_search_users_by_username(self):
        """Test searching users by username."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "jane"})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.count, 1)
        self.assertEqual(page_obj.object_list[0].username, "@janedoe")

    def test_search_users_by_first_name(self):
        """Test searching users by first name."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "Petra"})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.count, 1)
        self.assertEqual(page_obj.object_list[0].username, "@petrapickles")

    def test_search_users_by_last_name(self):
        """Test searching users by last name."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "Pickles"})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        # Both petra and peter have last name Pickles
        self.assertEqual(page_obj.paginator.count, 2)

    def test_search_users_case_insensitive(self):
        """Test that search is case insensitive."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "JANE"})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.count, 1)
        self.assertEqual(page_obj.object_list[0].username, "@janedoe")

    def test_search_users_partial_match(self):
        """Test that search matches partial strings."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "pick"})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        # Should match both petrapickles and peterpickles
        self.assertEqual(page_obj.paginator.count, 2)

    def test_search_users_no_results(self):
        """Test search with no matching results."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "nonexistentuser"})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.count, 0)

    def test_search_users_search_term_preserved(self):
        """Test that search term is preserved in context."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "jane"})
        self.assertEqual(response.status_code, 200)

        search_term = response.context["search_term"]
        self.assertEqual(search_term, "jane")

    def test_search_users_search_term_stripped(self):
        """Test that search term whitespace is stripped."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "  jane  "})
        self.assertEqual(response.status_code, 200)

        search_term = response.context["search_term"]
        self.assertEqual(search_term, "jane")

    def test_search_users_is_followed_attribute_when_not_following(self):
        """Test that users have is_followed=False when not following them."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        for user in page_obj.object_list:
            self.assertFalse(user.is_followed)

    def test_search_users_is_followed_attribute_when_following(self):
        """Test that users have is_followed=True when following them."""
        # Create follow relationship: johndoe follows janedoe
        Follow.objects.create(follower=self.user, following=self.other_user)

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        for user in page_obj.object_list:
            if user.id == self.other_user.id:
                self.assertTrue(user.is_followed)
            else:
                self.assertFalse(user.is_followed)

    def test_search_users_pagination_25_per_page(self):
        """Test that pagination shows 25 users per page."""
        # Create 30 additional users
        for i in range(30):
            User.objects.create_user(
                username=f"@testuser{i}",
                email=f"testuser{i}@example.org",
                password="Password123",
                first_name=f"Test{i}",
                last_name=f"User{i}",
            )

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        # Should show 25 users on first page
        self.assertEqual(len(page_obj.object_list), 25)
        # Total should be 33 (3 from fixtures + 30 created)
        self.assertEqual(page_obj.paginator.count, 33)

    def test_search_users_pagination_page_2(self):
        """Test accessing second page of pagination."""
        # Create 30 additional users
        for i in range(30):
            User.objects.create_user(
                username=f"@testuser{i}",
                email=f"testuser{i}@example.org",
                password="Password123",
                first_name=f"Test{i}",
                last_name=f"User{i}",
            )

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"page": 2})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        # Should show remaining 8 users on second page (33 - 25 = 8)
        self.assertEqual(len(page_obj.object_list), 8)
        self.assertEqual(page_obj.number, 2)

    def test_search_users_pagination_has_next(self):
        """Test pagination has_next property."""
        # Create 30 additional users
        for i in range(30):
            User.objects.create_user(
                username=f"@testuser{i}",
                email=f"testuser{i}@example.org",
                password="Password123",
                first_name=f"Test{i}",
                last_name=f"User{i}",
            )

        self.client.login(username=self.user.username, password="Password123")

        # First page should have next
        response = self.client.get(self.url, {"page": 1})
        page_obj = response.context["page_obj"]
        self.assertTrue(page_obj.has_next())

        # Last page should not have next
        response = self.client.get(self.url, {"page": 2})
        page_obj = response.context["page_obj"]
        self.assertFalse(page_obj.has_next())

    def test_search_users_pagination_has_previous(self):
        """Test pagination has_previous property."""
        # Create 30 additional users
        for i in range(30):
            User.objects.create_user(
                username=f"@testuser{i}",
                email=f"testuser{i}@example.org",
                password="Password123",
                first_name=f"Test{i}",
                last_name=f"User{i}",
            )

        self.client.login(username=self.user.username, password="Password123")

        # First page should not have previous
        response = self.client.get(self.url, {"page": 1})
        page_obj = response.context["page_obj"]
        self.assertFalse(page_obj.has_previous())

        # Second page should have previous
        response = self.client.get(self.url, {"page": 2})
        page_obj = response.context["page_obj"]
        self.assertTrue(page_obj.has_previous())

    def test_search_users_pagination_invalid_page(self):
        """Test that invalid page number defaults to first page."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"page": "invalid"})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.number, 1)

    def test_search_users_pagination_out_of_range(self):
        """Test that out of range page number returns last page."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"page": 999})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        # Should return the last page (page 1 with only 3 users)
        self.assertEqual(page_obj.number, 1)

    def test_search_users_search_with_pagination(self):
        """Test that search works correctly with pagination."""
        # Create 30 users with 'test' in their name
        for i in range(30):
            User.objects.create_user(
                username=f"@searchtest{i}",
                email=f"searchtest{i}@example.org",
                password="Password123",
                first_name=f"SearchTest{i}",
                last_name="SearchUser",
            )

        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, {"search": "searchtest", "page": 1})
        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.count, 30)
        self.assertEqual(len(page_obj.object_list), 25)

    def test_search_users_displays_usernames(self):
        """Test that usernames are displayed in the response."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "@janedoe")
        self.assertContains(response, "@petrapickles")
        self.assertContains(response, "@peterpickles")

    def test_search_users_does_not_display_current_user(self):
        """Test that current user's username is not displayed."""
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Check the page_obj doesn't contain current user
        page_obj = response.context["page_obj"]
        usernames = [u.username for u in page_obj.object_list]
        self.assertNotIn("@johndoe", usernames)

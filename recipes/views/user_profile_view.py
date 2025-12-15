from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse
from recipes.forms import UserForm
from django.db.models import Count, Prefetch, Q, Avg
from recipes.models import Recipe, Comment


class UserProfileView(LoginRequiredMixin, UpdateView):
    """
    Allow authenticated users to view their profile information.

    This class-based view displays a user profile editing form and handles
    updates to the authenticated user’s profile. Access is restricted to
    logged-in users via `LoginRequiredMixin`.
    """

    # model = UserForm
    template_name = "user_profile.html"
    form_class = UserForm

    def get_object(self):
        """Return the logged-in user's own profile."""
        return self.request.user

    def get_context_data(self, **kwargs):
        """Add followers and following lists to the template context."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # These come from the Follow model's related_name values:
        # follower_relations = users who follow this user
        # following_relations = users this user is following
        context["following_relations"] = user.following_relations.select_related(
            "following"
        ).all()

        context["followers_relations"] = user.follower_relations.select_related(
            "follower"
        ).all()

        top_comment_prefetch = Prefetch(
            "comments",
            queryset=Comment.objects.select_related("author")
            .annotate(likes_count=Count("likes"))
            .order_by("-likes_count", "-created_at")[:1],
            to_attr="top_comment_list",
        )

        user_recipes = (
            user.recipes.filter(visibility=Recipe.Visibility.PUBLIC)
            .select_related("author")
            .prefetch_related(top_comment_prefetch, "comments", "ratings")
            .annotate(
                total_comments=Count("comments", distinct=True),
                average_rating=Avg("ratings__rating"),
                rating_count=Count("ratings", distinct=True),
            )
        )

        for recipe in user_recipes:
            recipe.top_comment = (
                recipe.top_comment_list[0]
                if hasattr(recipe, "top_comment_list") and recipe.top_comment_list
                else None
            )

        # Add user's own recipes
        context["user_recipes"] = user_recipes

        return context

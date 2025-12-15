from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse
from recipes.forms import UserForm


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

        # These come from your Follow model's related_name values:
        # follower_relations = users who follow this user
        # following_relations = users THIS user is following
        context["following_relations"] = user.following_relations.select_related(
            "following"
        ).all()

        context["followers_relations"] = user.follower_relations.select_related(
            "follower"
        ).all()

        # Add user's own recipes
        context["user_recipes"] = user.recipes.all()

        return context

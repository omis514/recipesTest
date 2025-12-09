from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar


class User(AbstractUser):
    """Model used for user authentication, and team member related information."""

    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^@\w{3,}$",
                message="Username must consist of @ followed by at least three alphanumericals",
            )
        ],
    )
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)
    bio = models.CharField(max_length=500, blank=True)
    recipes_favourited_num = models.IntegerField(default=0, blank=False)
    preferred_spiceness = models.FloatField(
        default=1.5, blank=False, help_text="The user's preferred spiceness level"
    )
    preferred_cuisine = models.FloatField(
        null=True, blank=True, help_text="The user's preferred cuisine id"
    )

    class Meta:
        """Model options."""

        ordering = ["last_name", "first_name"]

    # Helper methods

    def full_name(self):
        """Return a string containing the user's full name."""

        return f"{self.first_name} {self.last_name}"

    def gravatar(self, size=120):
        """Return a URL to the user's gravatar."""

        gravatar_object = Gravatar(self.email)
        gravatar_url = gravatar_object.get_image(size=size, default="mp")
        return gravatar_url

    def mini_gravatar(self):
        """Return a URL to a miniature version of the user's gravatar."""

        return self.gravatar(size=60)

    # Follow relationships

    def followers(self):
        """Return all of the accounts that follow this user."""
        from .follow import Follow

        return (
            Follow.objects.filter(following=self)
            .select_related("follower")
            .order_by("follower__last_name", "follower__first_name")
        )

    def following(self):
        """Return all of the accounts that this user follows themselves."""
        from .follow import Follow

        return (
            Follow.objects.filter(follower=self)
            .select_related("following")
            .order_by("following__last_name", "following__first_name")
        )

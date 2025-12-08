from django.db import models


class Follow(models.Model):
    follower = models.ForeignKey(
        "recipes.User", related_name="following_relations", on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        "recipes.User", related_name="follower_relations", on_delete=models.CASCADE
    )
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")
        ordering = ["-followed_at"]

    def __str__(self):
        return f"{self.follower} follows {self.following}"

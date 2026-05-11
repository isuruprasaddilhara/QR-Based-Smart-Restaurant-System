from django.db import models

from users.models import User
from menu.models import MenuItem


class FavoriteMenuItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "menu_item"],
                name="uniq_favourite_user_menu_item",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.menu_item.name}"

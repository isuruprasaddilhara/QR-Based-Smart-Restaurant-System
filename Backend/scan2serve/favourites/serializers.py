from rest_framework import serializers

from menu.serializers import MenuSerializer
from .models import FavoriteMenuItem


class FavoriteMenuItemSerializer(serializers.ModelSerializer):
    menu_item_detail = MenuSerializer(source="menu_item", read_only=True)

    class Meta:
        model = FavoriteMenuItem
        fields = ["id", "menu_item", "menu_item_detail", "created_at"]
        read_only_fields = ["id", "created_at"]

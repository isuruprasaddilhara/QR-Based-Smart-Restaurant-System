from django.contrib import admin

from .models import FavoriteMenuItem


@admin.register(FavoriteMenuItem)
class FavoriteMenuItemAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "menu_item", "created_at")
    list_filter = ("created_at",)

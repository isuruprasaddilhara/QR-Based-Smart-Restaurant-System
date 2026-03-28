from rest_framework import serializers
from .models import MenuCategory, MenuItem

class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'category', 'availability', 'image_url', 'ingredients']
        read_only_fields = ['id']

class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ['id', 'name']
        read_only_fields = ['id']
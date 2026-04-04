from rest_framework import serializers
from .models import MenuCategory, MenuItem

class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'category', 'availability', 'image_url', 'ingredients']
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        if not request:
            return

        fields = request.query_params.get('fields')

        if fields:
            allowed_fields = set(fields.split(','))
            existing_fields = set(self.fields)

            for field in existing_fields - allowed_fields:
                self.fields.pop(field)

class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ['id', 'name']
        read_only_fields = ['id']
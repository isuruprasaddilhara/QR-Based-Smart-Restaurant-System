from rest_framework import serializers
from .models import MenuCategory, MenuItem

class MenuSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()  # reads from get_image_url()
    image = serializers.ImageField(write_only=True, required=False)  # accepts file upload, hidden from GET response

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'category', 'availability', 'image', 'image_url', 'ingredients']
        read_only_fields = ['id', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_ingredients(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("Ingredients cannot be empty.")
        return value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if not request:
            return
        fields = request.query_params.get('fields')
        if fields:
            allowed = set(fields.split(','))
            existing = set(self.fields.keys())
            for field in existing - allowed:
                self.fields.pop(field)

class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ['id', 'name']
        read_only_fields = ['id']
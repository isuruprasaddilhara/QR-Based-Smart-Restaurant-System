# tables/serializers.py
from rest_framework import serializers
from .models import Table

class TableSerializer(serializers.ModelSerializer):
    qr_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = ['id', 'qr_code', 'qr_image_url', 'status']
        read_only_fields = ['qr_code', 'qr_image_url']

    def get_qr_image_url(self, obj):
        request = self.context.get('request')
        if obj.qr_image and request:
            return request.build_absolute_uri(obj.qr_image.url)
        return None
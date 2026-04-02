from rest_framework import serializers
from .models import Table

class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ['id', 'qr_code', 'status', 'section', 'capacity']
        # read_only_fields = ['qr_code']

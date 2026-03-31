from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        refresh = RefreshToken.for_user(user)

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'role': user.role,
            'username': user.email
        }

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'name', 'password', 'role', 'phone_no')

    def validate_role(self, value):
        request = self.context.get('request')
        restricted_roles = ['kitchen', 'cashier', 'admin']

        if value in restricted_roles:
            # Must be authenticated and be an admin
            if not request or not request.user.is_authenticated:
                raise serializers.ValidationError("You must be logged in to assign this role.")
            if request.user.role != 'admin':
                raise serializers.ValidationError("Only admins can assign this role.")

        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
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

# serializers.py

class CustomerRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'name', 'password', 'phone_no')

    def create(self, validated_data):
        validated_data['role'] = 'customer'  # Force role, never trust client input
        user = User.objects.create_user(**validated_data)
        return user


class StaffRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['kitchen', 'cashier', 'admin'])

    class Meta:
        model = User
        fields = ('email', 'name', 'password', 'role', 'phone_no')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class CustomerEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'name', 'phone_no')
        extra_kwargs = {
            'email': {'required': False},
            'name': {'required': False},
            'phone_no': {'required': False},
        }

    

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class StaffEditSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=['kitchen', 'cashier', 'admin'], required=False)

    class Meta:
        model = User
        fields = ('email', 'name', 'phone_no', 'role')
        extra_kwargs = {
            'email': {'required': False},
            'name': {'required': False},
            'phone_no': {'required': False},
        }
    
    def validate_role(self, value):
        request = self.context.get('request')
        if request and request.user.role != 'admin':
            raise serializers.ValidationError("You do not have permission to change your role.")
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # We don't reveal whether the email exists — just silently succeed
        return value

    def save(self):
        email = self.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None  # Silent — don't leak user existence

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        return {'uid': uid, 'token': token, 'user': user}


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            uid = force_str(urlsafe_base64_decode(data['uid']))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError("Invalid reset link.")

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, data['token']):
            raise serializers.ValidationError("Reset link is invalid or has expired.")

        data['user'] = user
        return data

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
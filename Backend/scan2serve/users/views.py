from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (LoginSerializer, 
CustomerRegisterSerializer, 
StaffRegisterSerializer, 
CustomerEditSerializer, 
StaffEditSerializer, 
PasswordChangeSerializer,
ForgotPasswordSerializer,
PasswordResetConfirmSerializer,
UserSerializer)
from users.permissions import IsAdmin
from rest_framework.permissions import IsAuthenticated
from users.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from scan2serve.throttles import LoginAnonThrottle, LoginUserThrottle, RegisterThrottle, PasswordResetThrottle

class LoginView(APIView):
    throttle_classes = [LoginAnonThrottle, LoginUserThrottle]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            data = {
                "message": "Login successful",
                "user": serializer.validated_data
            }
            return Response(data, status=status.HTTP_200_OK)

        return Response({
            "message": "Login failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {'detail': 'Invalid or already blacklisted token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'detail': 'Logged out successfully.'},
            status=status.HTTP_205_RESET_CONTENT,
        )

class CustomerRegisterView(APIView):
    """Public endpoint — no authentication required."""
    throttle_classes = [RegisterThrottle]
    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User created successfully",
                "username": user.email,
                "name": user.name,
                "role": user.role
            }, status=status.HTTP_201_CREATED)

        return Response({
            "message": "User registration failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class StaffRegisterView(APIView):
    throttle_classes = [RegisterThrottle]
    permission_classes = [IsAdmin]
    def post(self, request):
        serializer = StaffRegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Staff account created successfully",
                "username": user.email,
                "name": user.name,
                "role": user.role
            }, status=status.HTTP_201_CREATED)

        return Response({
            "message": "Staff registration failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ── Customer: edit own profile ──────────────────────────────────────────────

class CustomerEditView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        # Customers can only edit themselves
        if request.user.role != 'customer':
            return Response(
                {'detail': 'Only customers can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CustomerEditSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Staff: admin edits any staff member ─────────────────────────────────────

class StaffEditView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, user_id=None):  
        target_id = user_id if user_id is not None else request.user.id
        try:
            staff = User.objects.get(id=target_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if staff.role == 'customer':
            return Response(
                {'detail': 'Use the customer endpoint to edit customers.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
         # Allow edit only if the requester is an admin OR editing their own profile
        if not request.user.role == 'admin' and request.user.id != target_id:
            return Response(
                {'detail': 'You do not have permission to edit other staff members.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StaffEditSerializer (staff, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Password change (any authenticated user) ─────────────────────────────────

class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            return Response(
                {'detail': 'Password updated successfully.'},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Delete views ──────────────────────────────────────────────────────────────

class CustomerDeleteView(APIView):
    """Customer deletes their own account."""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        if request.user.role != 'customer':
            return Response(
                {'detail': 'Only customers can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Blacklist the refresh token so it can't be reused
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass  # Already blacklisted or invalid — still delete the user

        request.user.delete()
        return Response(
            {'detail': 'Account deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT,
        )


class StaffDeleteView(APIView):
    #Admin can deletes any staff account. Staff can delete their own account but not other staff accounts.
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id=None):  # user_id optional
        target_id = user_id if user_id is not None else request.user.id  # fallback to self

        try:
            staff = User.objects.get(id=target_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if staff.role == 'customer':
            return Response(
                {'detail': 'Use the customer endpoint to delete customers.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.role == 'admin' and request.user.id != target_id:
            return Response(
                {'detail': 'You do not have permission to delete other staff members.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if staff == request.user and request.user.role == 'admin':
            return Response(
                {'detail': 'Admins cannot delete their own account here.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        staff.delete()
        return Response(
            {'detail': f'Staff member {staff.email} deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT,
        )

from django.core.mail import send_mail
from django.conf import settings

class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        if result:
            reset_link = f"https://scan2serve-frontend-ix17.onrender.com/reset-password-confirm?uid={result['uid']}&token={result['token']}"
            # f"http://localhost:3000/users/auth/reset-password/?uid={result['uid']}&token={result['token']}"

            send_mail(
                subject='Password Reset Request',
                message=f'Click the link to reset your password: {reset_link}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[result['user'].email],
                fail_silently=False,
            )

        return Response(
            {'detail': 'If that email exists, a reset link has been sent.'},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    throttle_classes = [PasswordResetThrottle]
    #Public endpoint — takes uid + token + new_password. No authentication required.

    def post(self, request):
        data = {
            'uid': request.query_params.get('uid'),
            'token': request.query_params.get('token'),
            'new_password': request.data.get('new_password'),
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'detail': 'Password has been reset successfully.'},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]  # Only admin can view staff

    def get(self, request):
        staff_users = User.objects.exclude(role='customer').exclude(id=request.user.id )
        serializer = UserSerializer(staff_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None):
        target_id = user_id if user_id is not None else request.user.id

        try:
            user = User.objects.get(id=target_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Do not allow this endpoint for customers
        if user.role == 'customer':
            return Response(
                {'detail': 'This endpoint is only for staff users.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Admin can view any staff user
        # Non-admin staff can only view themselves
        if request.user.role != 'admin' and request.user.id != user.id:
            return Response(
                {'detail': 'You do not have permission to view this user.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
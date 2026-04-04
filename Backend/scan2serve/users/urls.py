from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),  
    path('auth/register/customer/', views.CustomerRegisterView.as_view(), name='customer-register'),
    path('auth/register/staff/', views.StaffRegisterView.as_view(), name='staff-register'),
    path('customer/edit/' ,views.CustomerEditView.as_view(),   name='customer-edit'),
    path('customer/delete/' ,views.CustomerDeleteView.as_view(), name='customer-delete'),
    path('staff/edit/<int:user_id>/' ,views.StaffEditView.as_view(), name='staff-edit'),
    path('staff/edit/', views.StaffEditView.as_view(), name='staff-edit'),
    path('staff/delete/<int:user_id>/' , views.StaffDeleteView.as_view(),name='staff-delete'),
    path('staff/delete/', views.StaffDeleteView.as_view(), name='staff-delete'),
    path('auth/password/change/',views.PasswordChangeView.as_view(), name='password-change'),
    path('auth/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/reset-password/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]

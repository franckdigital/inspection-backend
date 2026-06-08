from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, CustomTokenObtainPairView, UserDetailView,
    ChangePasswordView, PasswordResetRequestView, PasswordResetConfirmView,
    EmailVerificationView, SetupOTPView, DisableOTPView, VerifyOTPView,
    EmployeeProfileView, InspectorProfileView, EmployerProfileView,
    EmployeeInspectorAssignView,
)

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User Management
    path('me/', UserDetailView.as_view(), name='user_detail'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

    # Password Reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # Email Verification
    path('verify-email/', EmailVerificationView.as_view(), name='verify_email'),

    # OTP
    path('otp/setup/', SetupOTPView.as_view(), name='otp_setup'),
    path('otp/verify/', VerifyOTPView.as_view(), name='otp_verify'),
    path('otp/disable/', DisableOTPView.as_view(), name='otp_disable'),

    # Profiles
    path('profile/employee/', EmployeeProfileView.as_view(), name='employee_profile'),
    path('profile/inspector/', InspectorProfileView.as_view(), name='inspector_profile'),
    path('profile/employer/', EmployerProfileView.as_view(), name='employer_profile'),

    # Admin — affectation inspecteur aux salariés (sans contrat)
    path('employees/unassigned/', EmployeeInspectorAssignView.as_view(), name='employees_unassigned'),
    path('employees/<int:employee_id>/assign-inspector/', EmployeeInspectorAssignView.as_view(), name='employee_assign_inspector'),
    path('employees/bulk-auto-assign/', EmployeeInspectorAssignView.as_view(), name='employees_bulk_assign'),
]

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmployeeProfile, InspectorProfile, EmployerProfile, PasswordReset, EmailVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_verified', 'created_at')
    list_filter = ('user_type', 'is_active', 'is_verified', 'otp_enabled')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'gender', 'date_of_birth', 'phone_number', 'profile_picture')}),
        ('Type d\'utilisateur', {'fields': ('user_type',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Sécurité', {'fields': ('otp_enabled', 'otp_secret')}),
        ('Dates importantes', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'last_login')


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'national_id', 'job_title', 'current_employer', 'hire_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'national_id')
    list_filter = ('hire_date', 'city')


@admin.register(InspectorProfile)
class InspectorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge_number', 'inspection_zone', 'specialization')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'badge_number')
    list_filter = ('inspection_zone', 'specialization')


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employer_type', 'enterprise', 'position')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('employer_type',)


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'used')
    list_filter = ('used', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'verified')
    list_filter = ('verified', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)

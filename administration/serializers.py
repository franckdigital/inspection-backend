from rest_framework import serializers
from .models import SystemConfiguration, AuditLog, BackupLog, MaintenanceMode, Permission, Role, RolePermission
from users.models import User


class SystemConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfiguration
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ('created_at',)


class BackupLogSerializer(serializers.ModelSerializer):
    triggered_by_name = serializers.CharField(source='triggered_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = BackupLog
        fields = '__all__'
        read_only_fields = ('created_at',)


class MaintenanceModeSerializer(serializers.ModelSerializer):
    activated_by_name = serializers.CharField(source='activated_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = MaintenanceMode
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    permissions_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = '__all__'

    def get_permissions_count(self, obj):
        return obj.permissions.count()


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'permission', 'description']


class UserAdminSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'user_type', 'is_active', 'is_verified',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class UserAdminCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'user_type', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.is_verified = True
        user.save()
        return user

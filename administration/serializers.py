from rest_framework import serializers
from .models import SystemConfiguration, AuditLog, BackupLog, MaintenanceMode, Permission, Role


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

from django.contrib import admin
from .models import SystemConfiguration, AuditLog, BackupLog, MaintenanceMode, Permission, Role


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'config_type', 'value_preview', 'is_active', 'updated_at')
    list_filter = ('config_type', 'is_active')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')

    def value_preview(self, obj):
        return obj.value[:50]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_repr', 'created_at')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('user__email', 'object_repr')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)


@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ('backup_type', 'status', 'file_size_mb', 'started_at', 'completed_at')
    list_filter = ('backup_type', 'status', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('triggered_by',)


@admin.register(MaintenanceMode)
class MaintenanceModeAdmin(admin.ModelAdmin):
    list_display = ('is_active', 'activated_at', 'deactivated_at', 'activated_by')
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('activated_by', 'deactivated_by')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'module', 'is_active')
    list_filter = ('module', 'is_active')
    search_fields = ('code', 'name')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'permissions_count', 'is_system', 'is_active')
    list_filter = ('is_system', 'is_active')
    search_fields = ('name', 'code')
    filter_horizontal = ('permissions',)

    def permissions_count(self, obj):
        return obj.permissions.count()

from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import (
    SystemConfigurationViewSet, AuditLogViewSet, BackupLogViewSet,
    MaintenanceModeViewSet, PermissionViewSet, RoleViewSet,
    RolePermissionViewSet, UserAdminViewSet,
)

app_name = 'administration'

router = SimpleRouter()
router.register(r'config', SystemConfigurationViewSet, basename='config')
router.register(r'audit', AuditLogViewSet, basename='audit')
router.register(r'backups', BackupLogViewSet, basename='backup')
router.register(r'maintenance', MaintenanceModeViewSet, basename='maintenance')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'role-permissions', RolePermissionViewSet, basename='role-permissions')
router.register(r'users', UserAdminViewSet, basename='admin-users')

urlpatterns = router.urls

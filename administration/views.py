from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count

from .models import SystemConfiguration, AuditLog, BackupLog, MaintenanceMode, Permission, Role
from .serializers import (
    SystemConfigurationSerializer, AuditLogSerializer, BackupLogSerializer,
    MaintenanceModeSerializer, PermissionSerializer, RoleSerializer
)


class SystemConfigurationViewSet(viewsets.ModelViewSet):
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiques d'audit"""
        stats = AuditLog.objects.values('action').annotate(count=Count('id'))

        return Response({
            'total': AuditLog.objects.count(),
            'by_action': list(stats)
        })


class BackupLogViewSet(viewsets.ModelViewSet):
    queryset = BackupLog.objects.all()
    serializer_class = BackupLogSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['post'])
    def trigger_backup(self, request):
        """Déclencher une sauvegarde"""
        backup_type = request.data.get('backup_type', 'FULL')

        backup = BackupLog.objects.create(
            backup_type=backup_type,
            status='PENDING',
            triggered_by=request.user
        )

        # En production: lancer tâche Celery pour backup
        # backup_task.delay(backup.id)

        return Response({
            'message': 'Sauvegarde lancée',
            'backup_id': backup.id
        })


class MaintenanceModeViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceMode.objects.all()
    serializer_class = MaintenanceModeSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['post'])
    def activate(self, request):
        """Activer le mode maintenance"""
        message = request.data.get('message', 'Système en maintenance.')

        maintenance = MaintenanceMode.objects.create(
            is_active=True,
            message=message,
            activated_by=request.user,
            activated_at=timezone.now()
        )

        return Response({'message': 'Mode maintenance activé'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactiver le mode maintenance"""
        maintenance = self.get_object()
        maintenance.is_active = False
        maintenance.deactivated_by = request.user
        maintenance.deactivated_at = timezone.now()
        maintenance.save()

        return Response({'message': 'Mode maintenance désactivé'})


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAdminUser]


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAdminUser]

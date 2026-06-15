from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count

from .models import SystemConfiguration, AuditLog, BackupLog, MaintenanceMode, Permission, Role, RolePermission
from .serializers import (
    SystemConfigurationSerializer, AuditLogSerializer, BackupLogSerializer,
    MaintenanceModeSerializer, PermissionSerializer, RoleSerializer,
    RolePermissionSerializer, UserAdminSerializer, UserAdminCreateSerializer,
)
from users.models import User
from core.permissions import IsAdmin


class SystemConfigurationViewSet(viewsets.ModelViewSet):
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    permission_classes = [IsAdmin]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdmin]


class RolePermissionViewSet(viewsets.ModelViewSet):
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAdmin]

    @action(detail=False, methods=['post'])
    def save_matrix(self, request):
        """Remplace toute la matrice depuis le frontend (localStorage sync)"""
        matrix = request.data.get('matrix', {})

        RolePermission.objects.all().delete()

        to_create = [
            RolePermission(role=role_key, permission=perm_key)
            for role_key, perms in matrix.items()
            for perm_key, granted in perms.items()
            if granted
        ]
        RolePermission.objects.bulk_create(to_create, ignore_conflicts=True)

        return Response({'message': 'Matrice enregistrée', 'count': len(to_create)})


class UserAdminViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('last_name', 'first_name')
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserAdminCreateSerializer
        return UserAdminSerializer

    def get_queryset(self):
        qs = User.objects.all().order_by('last_name', 'first_name')
        q = self.request.query_params.get('q', '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) |
                Q(email__icontains=q) | Q(phone_number__icontains=q)
            )
        return qs

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import WorkflowApproval, Escalation, Delegation, ReassignmentHistory
from .serializers import (
    WorkflowApprovalSerializer, ApproveRejectSerializer,
    EscalationSerializer, EscalateComplaintSerializer,
    DelegationSerializer, ReassignmentHistorySerializer,
    ReassignComplaintSerializer
)
from complaints.models import Complaint, ComplaintStatusHistory, ComplaintNotification
from users.models import User
from core.permissions import IsChefInspection, IsInspecteur


class WorkflowApprovalViewSet(viewsets.ModelViewSet):
    queryset = WorkflowApproval.objects.all()
    serializer_class = WorkflowApprovalSerializer
    permission_classes = [IsChefInspection]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'level', 'approver', 'complaint']

    def get_queryset(self):
        user = self.request.user
        queryset = WorkflowApproval.objects.all()

        # Filtrer selon le rôle
        if user.user_type in ['CHEF_INSPECTION', 'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL']:
            queryset = queryset.filter(approver=user)

        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approuver un dossier"""
        approval = self.get_object()

        if approval.approver != request.user:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à approuver ce dossier'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ApproveRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approval.status = 'APPROVED'
        approval.comment = serializer.validated_data.get('comment', '')
        approval.approved_at = timezone.now()
        approval.save()

        # Mettre à jour le statut de la plainte
        approval.complaint.status = 'IN_PROGRESS'
        approval.complaint.save()

        # Créer historique
        ComplaintStatusHistory.objects.create(
            complaint=approval.complaint,
            from_status=approval.complaint.status,
            to_status='IN_PROGRESS',
            changed_by=request.user,
            reason=f'Approuvé par {approval.get_level_display()}'
        )

        # Notifier l'inspecteur
        if approval.complaint.assigned_to:
            ComplaintNotification.objects.create(
                complaint=approval.complaint,
                recipient=approval.complaint.assigned_to,
                message=f'Votre dossier {approval.complaint.complaint_number} a été approuvé'
            )

        return Response({'message': 'Dossier approuvé avec succès'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejeter un dossier"""
        approval = self.get_object()

        if approval.approver != request.user:
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à rejeter ce dossier'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ApproveRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approval.status = 'REJECTED'
        approval.comment = serializer.validated_data.get('comment', '')
        approval.approved_at = timezone.now()
        approval.save()

        # Créer historique
        ComplaintStatusHistory.objects.create(
            complaint=approval.complaint,
            from_status=approval.complaint.status,
            to_status=approval.complaint.status,
            changed_by=request.user,
            reason=f'Rejeté par {approval.get_level_display()}: {approval.comment}'
        )

        # Notifier l'inspecteur
        if approval.complaint.assigned_to:
            ComplaintNotification.objects.create(
                complaint=approval.complaint,
                recipient=approval.complaint.assigned_to,
                message=f'Votre dossier {approval.complaint.complaint_number} a été rejeté'
            )

        return Response({'message': 'Dossier rejeté'})

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Dossiers en attente d'approbation"""
        queryset = self.get_queryset().filter(
            status='PENDING',
            approver=request.user
        ).order_by('-created_at')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class EscalationViewSet(viewsets.ModelViewSet):
    queryset = Escalation.objects.all()
    serializer_class = EscalationSerializer
    permission_classes = [IsInspecteur]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reason', 'is_resolved', 'complaint']

    @action(detail=False, methods=['post'])
    def escalate_complaint(self, request):
        """Escalader une plainte"""
        complaint_id = request.data.get('complaint_id')
        serializer = EscalateComplaintSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            complaint = Complaint.objects.get(id=complaint_id)
            to_user = User.objects.get(id=serializer.validated_data['to_user_id'])

            # Créer l'escalade
            escalation = Escalation.objects.create(
                complaint=complaint,
                from_user=request.user,
                to_user=to_user,
                reason=serializer.validated_data['reason'],
                description=serializer.validated_data['description']
            )

            # Changer le statut
            old_status = complaint.status
            complaint.status = 'ESCALATED'
            complaint.save()

            # Historique
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                from_status=old_status,
                to_status='ESCALATED',
                changed_by=request.user,
                reason=f'Escaladé vers {to_user.get_full_name()}'
            )

            # Notification
            ComplaintNotification.objects.create(
                complaint=complaint,
                recipient=to_user,
                message=f'Escalade: {complaint.complaint_number} - {escalation.get_reason_display()}'
            )

            return Response({
                'message': 'Plainte escaladée avec succès',
                'escalation': EscalationSerializer(escalation).data
            })

        except Complaint.DoesNotExist:
            return Response({'error': 'Plainte non trouvée'}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Résoudre une escalade"""
        escalation = self.get_object()
        escalation.is_resolved = True
        escalation.resolved_at = timezone.now()
        escalation.save()

        return Response({'message': 'Escalade résolue'})


class DelegationViewSet(viewsets.ModelViewSet):
    queryset = Delegation.objects.all()
    serializer_class = DelegationSerializer
    permission_classes = [IsChefInspection]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'from_user', 'to_user']

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Délégations actives"""
        today = timezone.now().date()
        queryset = self.queryset.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactiver une délégation"""
        delegation = self.get_object()
        delegation.is_active = False
        delegation.save()
        return Response({'message': 'Délégation désactivée'})


class ReassignmentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReassignmentHistory.objects.all()
    serializer_class = ReassignmentHistorySerializer
    permission_classes = [IsChefInspection]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['complaint', 'from_inspector', 'to_inspector']

    @action(detail=False, methods=['post'])
    def reassign_complaint(self, request):
        """Réaffecter une plainte"""
        complaint_id = request.data.get('complaint_id')
        serializer = ReassignComplaintSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            complaint = Complaint.objects.get(id=complaint_id)
            to_inspector = User.objects.get(
                id=serializer.validated_data['to_inspector_id'],
                user_type='INSPECTEUR'
            )

            old_inspector = complaint.assigned_to

            # Créer l'historique
            ReassignmentHistory.objects.create(
                complaint=complaint,
                from_inspector=old_inspector,
                to_inspector=to_inspector,
                reassigned_by=request.user,
                reason=serializer.validated_data['reason']
            )

            # Réaffecter
            complaint.assigned_to = to_inspector
            complaint.save()

            # Historique statut
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                from_status=complaint.status,
                to_status=complaint.status,
                changed_by=request.user,
                reason=f'Réaffecté de {old_inspector.get_full_name()} à {to_inspector.get_full_name()}'
            )

            # Notifications
            ComplaintNotification.objects.create(
                complaint=complaint,
                recipient=to_inspector,
                message=f'Nouvelle plainte assignée: {complaint.complaint_number}'
            )

            if old_inspector:
                ComplaintNotification.objects.create(
                    complaint=complaint,
                    recipient=old_inspector,
                    message=f'Plainte {complaint.complaint_number} réaffectée'
                )

            return Response({'message': 'Plainte réaffectée avec succès'})

        except Complaint.DoesNotExist:
            return Response({'error': 'Plainte non trouvée'}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({'error': 'Inspecteur non trouvé'}, status=status.HTTP_404_NOT_FOUND)


from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Complaint, ComplaintDocument, ComplaintComment, ComplaintStatusHistory, ComplaintNotification
from .serializers import (
    ComplaintSerializer, ComplaintDetailSerializer, ComplaintCreateSerializer,
    ComplaintDocumentSerializer, ComplaintCommentSerializer,
    ComplaintStatusHistorySerializer, ComplaintNotificationSerializer
)


class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'complaint_type', 'assigned_to', 'inspection_zone']
    search_fields = ['complaint_number', 'subject', 'description', 'employer_name']
    ordering_fields = ['created_at', 'updated_at', 'priority']

    def get_serializer_class(self):
        if self.action == 'create':
            return ComplaintCreateSerializer
        elif self.action == 'retrieve':
            return ComplaintDetailSerializer
        return ComplaintSerializer

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        queryset = Complaint.objects.all()

        if user.user_type == 'EMPLOYE':
            queryset = queryset.filter(complainant=user)
        elif user.user_type == 'EMPLOYE_MAISON':
            queryset = queryset.filter(complainant=user)
        elif user.user_type == 'INSPECTEUR':
            # Plaintes assignées + toutes les plaintes des employés de maison
            queryset = queryset.filter(
                Q(assigned_to=user) | Q(complainant__user_type='EMPLOYE_MAISON')
            )
        elif user.user_type in ['CHEF_INSPECTION', 'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL', 'ADMIN']:
            pass
        else:
            queryset = queryset.filter(complainant=user)

        return queryset

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        complaint = self.get_object()
        inspector_id = request.data.get('inspector_id')

        if not inspector_id:
            return Response(
                {'error': 'inspector_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from users.models import User
        try:
            inspector = User.objects.get(id=inspector_id, user_type='INSPECTEUR')
            old_status = complaint.status
            complaint.assigned_to = inspector
            complaint.status = 'ASSIGNED'
            complaint.save()

            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                from_status=old_status,
                to_status='ASSIGNED',
                changed_by=request.user,
                reason=f'Assigné à {inspector.get_full_name()}'
            )

            ComplaintNotification.objects.create(
                complaint=complaint,
                recipient=inspector,
                message=f'Une nouvelle plainte #{complaint.complaint_number} vous a été assignée'
            )

            return Response({'message': 'Plainte assignée avec succès'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Inspecteur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        complaint = self.get_object()
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')

        if not new_status:
            return Response(
                {'error': 'status est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = complaint.status
        complaint.status = new_status

        if new_status in ['RESOLVED', 'CLOSED']:
            complaint.closed_at = timezone.now()
            complaint.resolution = request.data.get('resolution', '')

        complaint.save()

        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            from_status=old_status,
            to_status=new_status,
            changed_by=request.user,
            reason=reason
        )

        ComplaintNotification.objects.create(
            complaint=complaint,
            recipient=complaint.complainant,
            message=f'Le statut de votre plainte #{complaint.complaint_number} a été mis à jour: {complaint.get_status_display()}'
        )

        return Response({'message': 'Statut mis à jour avec succès'})

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        complaint = self.get_object()
        documents = complaint.documents.all()
        serializer = ComplaintDocumentSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_document(self, request, pk=None):
        complaint = self.get_object()
        serializer = ComplaintDocumentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(complaint=complaint)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        complaint = self.get_object()
        comments = complaint.comments.all()

        if request.user == complaint.complainant:
            comments = comments.filter(is_internal=False)

        serializer = ComplaintCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        complaint = self.get_object()
        comment_text = request.data.get('comment')
        is_internal = request.data.get('is_internal', False)

        if not comment_text:
            return Response(
                {'error': 'comment est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        comment = ComplaintComment.objects.create(
            complaint=complaint,
            author=request.user,
            comment=comment_text,
            is_internal=is_internal
        )

        if not is_internal:
            recipients = [complaint.complainant]
            if complaint.assigned_to and complaint.assigned_to != request.user:
                recipients.append(complaint.assigned_to)

            for recipient in recipients:
                if recipient != request.user:
                    ComplaintNotification.objects.create(
                        complaint=complaint,
                        recipient=recipient,
                        message=f'Nouveau commentaire sur la plainte #{complaint.complaint_number}'
                    )

        serializer = ComplaintCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ComplaintNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ComplaintNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ComplaintNotification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return Response({'message': 'Notification marquée comme lue'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        ComplaintNotification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({'message': 'Toutes les notifications marquées comme lues'})

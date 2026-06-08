from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import JudicialProcedure, CourtDocument, Hearing, JudicialDecision
from .serializers import (
    JudicialProcedureSerializer, CourtDocumentSerializer,
    HearingSerializer, JudicialDecisionSerializer,
    TransmitToCourtSerializer
)
from complaints.models import ComplaintStatusHistory, ComplaintNotification


class JudicialProcedureViewSet(viewsets.ModelViewSet):
    queryset = JudicialProcedure.objects.all()
    serializer_class = JudicialProcedureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'procedure_type', 'plaintiff', 'case_officer']

    def perform_create(self, serializer):
        procedure = serializer.save()

        # Mettre à jour le statut de la plainte
        procedure.complaint.status = 'JUDICIAL'
        procedure.complaint.save()

        # Créer historique
        ComplaintStatusHistory.objects.create(
            complaint=procedure.complaint,
            from_status=procedure.complaint.status,
            to_status='JUDICIAL',
            changed_by=self.request.user,
            reason='Procédure judiciaire engagée'
        )

    @action(detail=True, methods=['post'])
    def transmit(self, request, pk=None):
        """Transmettre au tribunal"""
        procedure = self.get_object()
        serializer = TransmitToCourtSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        procedure.court_name = serializer.validated_data['court_name']
        procedure.submission_date = serializer.validated_data['submission_date']
        procedure.court_reference = serializer.validated_data.get('court_reference', '')
        procedure.status = 'SUBMITTED'
        procedure.save()

        # Notifier
        if procedure.plaintiff:
            ComplaintNotification.objects.create(
                complaint=procedure.complaint,
                recipient=procedure.plaintiff,
                message=f'Dossier transmis au tribunal: {procedure.court_name}'
            )

        return Response({'message': 'Dossier transmis au tribunal'})

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Liste des documents"""
        procedure = self.get_object()
        documents = procedure.documents.all()
        serializer = CourtDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Upload un document"""
        procedure = self.get_object()
        serializer = CourtDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(procedure=procedure, uploaded_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def hearings(self, request, pk=None):
        """Liste des audiences"""
        procedure = self.get_object()
        hearings = procedure.hearings.all()
        serializer = HearingSerializer(hearings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def schedule_hearing(self, request, pk=None):
        """Programmer une audience"""
        procedure = self.get_object()
        serializer = HearingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hearing = serializer.save(procedure=procedure)

        procedure.status = 'HEARING_SCHEDULED'
        procedure.save()

        return Response(HearingSerializer(hearing).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def decision(self, request, pk=None):
        """Récupérer la décision"""
        procedure = self.get_object()
        try:
            decision = procedure.decision
            serializer = JudicialDecisionSerializer(decision)
            return Response(serializer.data)
        except JudicialDecision.DoesNotExist:
            return Response(
                {'error': 'Aucune décision trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def record_decision(self, request, pk=None):
        """Enregistrer une décision"""
        procedure = self.get_object()
        serializer = JudicialDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.save(procedure=procedure)

        procedure.status = 'DECIDED'
        procedure.save()

        # Mettre à jour la plainte
        procedure.complaint.status = 'CLOSED'
        procedure.complaint.save()

        return Response(JudicialDecisionSerializer(decision).data, status=status.HTTP_201_CREATED)


class HearingViewSet(viewsets.ModelViewSet):
    queryset = Hearing.objects.all()
    serializer_class = HearingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'hearing_type', 'procedure']

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Marquer l'audience comme tenue"""
        hearing = self.get_object()
        hearing.status = 'COMPLETED'
        hearing.actual_date = timezone.now()
        hearing.plaintiff_present = request.data.get('plaintiff_present', False)
        hearing.defendant_present = request.data.get('defendant_present', False)
        hearing.minutes = request.data.get('minutes', '')
        hearing.next_steps = request.data.get('next_steps', '')
        hearing.save()

        return Response({'message': 'Audience marquée comme tenue'})

    @action(detail=True, methods=['post'])
    def postpone(self, request, pk=None):
        """Reporter l'audience"""
        hearing = self.get_object()
        new_date = request.data.get('new_date')
        if not new_date:
            return Response(
                {'error': 'Nouvelle date requise'},
                status=status.HTTP_400_BAD_REQUEST
            )

        hearing.status = 'POSTPONED'
        hearing.save()

        # Créer nouvelle audience
        new_hearing = Hearing.objects.create(
            procedure=hearing.procedure,
            hearing_type=hearing.hearing_type,
            scheduled_date=new_date,
            location=hearing.location,
            room=hearing.room,
            judge=hearing.judge
        )

        return Response(HearingSerializer(new_hearing).data)


class JudicialDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JudicialDecision.objects.all()
    serializer_class = JudicialDecisionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['decision_type', 'outcome', 'is_final']

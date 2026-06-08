from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Mediation, MediationParticipant, MediationMinutes,
    Agreement, MediationDocument
)
from .serializers import (
    MediationSerializer, MediationDetailSerializer,
    MediationParticipantSerializer, ConvokeParticipantsSerializer,
    MediationMinutesSerializer, GenerateMinutesSerializer,
    AgreementSerializer, CreateAgreementSerializer, SignAgreementSerializer,
    MediationDocumentSerializer
)
from complaints.models import Complaint, ComplaintStatusHistory, ComplaintNotification


class MediationViewSet(viewsets.ModelViewSet):
    queryset = Mediation.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'session_type', 'outcome', 'mediator', 'complaint']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MediationDetailSerializer
        return MediationSerializer

    def perform_create(self, serializer):
        mediation = serializer.save()

        # Mettre à jour le statut de la plainte
        mediation.complaint.status = 'MEDIATION'
        mediation.complaint.save()

        # Créer historique
        ComplaintStatusHistory.objects.create(
            complaint=mediation.complaint,
            from_status=mediation.complaint.status,
            to_status='MEDIATION',
            changed_by=self.request.user,
            reason='Séance de médiation programmée'
        )

    @action(detail=True, methods=['post'])
    def convoke(self, request, pk=None):
        """Convoquer les participants"""
        mediation = self.get_object()
        serializer = ConvokeParticipantsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        participant_ids = serializer.validated_data['participant_ids']
        send_email = serializer.validated_data.get('send_email', True)
        send_sms = serializer.validated_data.get('send_sms', False)

        convoked_count = 0
        for participant_id in participant_ids:
            try:
                participant = MediationParticipant.objects.get(id=participant_id, mediation=mediation)
                participant.convoked_at = timezone.now()
                participant.convocation_sent = True
                participant.save()

                # TODO: Envoyer email/SMS de convocation
                # if send_email:
                #     send_convocation_email(participant)
                # if send_sms:
                #     send_convocation_sms(participant)

                convoked_count += 1
            except MediationParticipant.DoesNotExist:
                continue

        return Response({
            'message': f'{convoked_count} participant(s) convoqué(s)',
            'convoked': convoked_count
        })

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Démarrer la séance"""
        mediation = self.get_object()
        mediation.status = 'ONGOING'
        mediation.save()

        return Response({'message': 'Séance de médiation démarrée'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Terminer la séance"""
        mediation = self.get_object()
        mediation.status = 'COMPLETED'
        mediation.completed_at = timezone.now()
        mediation.save()

        # Mettre à jour le statut de la plainte selon le résultat
        if mediation.outcome == 'AGREEMENT':
            mediation.complaint.status = 'RESOLVED'
        elif mediation.outcome == 'NO_AGREEMENT':
            mediation.complaint.status = 'JUDICIAL'

        mediation.complaint.save()

        return Response({'message': 'Séance de médiation terminée'})

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """Liste des participants"""
        mediation = self.get_object()
        participants = mediation.participants.all()
        serializer = MediationParticipantSerializer(participants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Ajouter un participant"""
        mediation = self.get_object()
        serializer = MediationParticipantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(mediation=mediation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def generate_minutes(self, request, pk=None):
        """Générer le procès-verbal"""
        mediation = self.get_object()
        serializer = GenerateMinutesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Créer ou mettre à jour le PV
        minutes, created = MediationMinutes.objects.get_or_create(
            mediation=mediation,
            defaults=serializer.validated_data
        )

        if not created:
            for key, value in serializer.validated_data.items():
                setattr(minutes, key, value)
            minutes.save()

        # TODO: Générer PDF du PV
        # minutes.pdf_file = generate_minutes_pdf(minutes)
        # minutes.save()

        return Response({
            'message': 'Procès-verbal généré',
            'minutes': MediationMinutesSerializer(minutes).data
        })

    @action(detail=True, methods=['get'])
    def minutes(self, request, pk=None):
        """Récupérer le procès-verbal"""
        mediation = self.get_object()
        try:
            minutes = mediation.minutes
            serializer = MediationMinutesSerializer(minutes)
            return Response(serializer.data)
        except MediationMinutes.DoesNotExist:
            return Response(
                {'error': 'Aucun procès-verbal trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def create_agreement(self, request, pk=None):
        """Créer un accord"""
        mediation = self.get_object()
        serializer = CreateAgreementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        agreement = Agreement.objects.create(
            mediation=mediation,
            **serializer.validated_data
        )

        return Response({
            'message': 'Accord créé',
            'agreement': AgreementSerializer(agreement).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def agreement(self, request, pk=None):
        """Récupérer l'accord"""
        mediation = self.get_object()
        try:
            agreement = mediation.agreement
            serializer = AgreementSerializer(agreement)
            return Response(serializer.data)
        except Agreement.DoesNotExist:
            return Response(
                {'error': 'Aucun accord trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def sign_agreement(self, request, pk=None):
        """Signer l'accord"""
        mediation = self.get_object()
        serializer = SignAgreementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            agreement = mediation.agreement
        except Agreement.DoesNotExist:
            return Response(
                {'error': 'Aucun accord à signer'},
                status=status.HTTP_404_NOT_FOUND
            )

        role = serializer.validated_data['signer_role']
        signature = serializer.validated_data['signature_image']

        if role == 'employee':
            agreement.employee_signature = signature
        elif role == 'employer':
            agreement.employer_signature = signature
        elif role == 'mediator':
            agreement.mediator_signature = signature

        agreement.save()

        # Si tout le monde a signé
        if agreement.is_fully_signed() and agreement.status == 'PENDING_SIGNATURE':
            agreement.status = 'SIGNED'
            agreement.signed_at = timezone.now()
            agreement.save()

            # Mettre à jour le résultat de la médiation
            mediation.outcome = 'AGREEMENT'
            mediation.save()

        return Response({
            'message': f'Signature {role} enregistrée',
            'is_fully_signed': agreement.is_fully_signed()
        })

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Liste des documents"""
        mediation = self.get_object()
        documents = mediation.documents.all()
        serializer = MediationDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Upload un document"""
        mediation = self.get_object()
        serializer = MediationDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(mediation=mediation, uploaded_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Médiations à venir"""
        queryset = self.queryset.filter(
            session_date__gte=timezone.now(),
            status='SCHEDULED'
        ).order_by('session_date')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_mediations(self, request):
        """Mes médiations (en tant que médiateur)"""
        queryset = self.queryset.filter(mediator=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MediationParticipantViewSet(viewsets.ModelViewSet):
    queryset = MediationParticipant.objects.all()
    serializer_class = MediationParticipantSerializer
    permission_classes = [permissions.IsAuthenticated]


class AgreementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Agreement.objects.all()
    serializer_class = AgreementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'mediation']

    @action(detail=True, methods=['post'])
    def mark_executed(self, request, pk=None):
        """Marquer comme exécuté"""
        agreement = self.get_object()
        agreement.status = 'EXECUTED'
        agreement.save()
        return Response({'message': 'Accord marqué comme exécuté'})

    @action(detail=True, methods=['post'])
    def mark_breached(self, request, pk=None):
        """Marquer comme violé"""
        agreement = self.get_object()
        agreement.status = 'BREACHED'
        agreement.save()

        # Créer notification pour le médiateur
        ComplaintNotification.objects.create(
            complaint=agreement.mediation.complaint,
            recipient=agreement.mediation.mediator,
            message=f'Accord violé - {agreement.mediation.complaint.complaint_number}'
        )

        return Response({'message': 'Accord marqué comme violé'})

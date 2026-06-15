from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Mediation, MediationParticipant, ConvocationAttempt,
    MediationMinutes, Agreement, MediationDocument
)
from .serializers import (
    MediationSerializer, MediationDetailSerializer,
    MediationParticipantSerializer,
    ConvokeParticipantsSerializer, AcknowledgeConvocationSerializer,
    ManualAcknowledgeSerializer, ReportNoShowSerializer, PostponeSerializer,
    MediationMinutesSerializer, GenerateMinutesSerializer,
    AgreementSerializer, CreateAgreementSerializer, SignAgreementSerializer,
    MediationDocumentSerializer,
)
from .notifications import (
    send_convocation_email, send_convocation_sms,
    send_convocation_inapp, notify_hierarchy_no_response,
)
from complaints.models import Complaint, ComplaintStatusHistory, ComplaintNotification
from core.permissions import IsInspecteur, IsInspecteurOrEmploye

# Délai légal (heures) avant de considérer une absence de réponse comme un refus
CONVOCATION_REPLY_DEADLINE_HOURS = 72
# Nombre max de tentatives avant escalade automatique
MAX_CONVOCATION_ATTEMPTS = 3


class MediationViewSet(viewsets.ModelViewSet):
    queryset = Mediation.objects.select_related(
        'complaint', 'mediator', 'no_show_reported_by'
    ).prefetch_related('participants', 'documents').all()
    permission_classes = [IsInspecteur]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'session_type', 'outcome', 'mediator',
                        'complaint', 'employer_no_show']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MediationDetailSerializer
        return MediationSerializer

    def perform_create(self, serializer):
        mediation = serializer.save()
        complaint = mediation.complaint
        prev_status = complaint.status
        complaint.status = 'MEDIATION'
        complaint.save()
        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            from_status=prev_status,
            to_status='MEDIATION',
            changed_by=self.request.user,
            reason='Séance de médiation programmée',
        )

    # ── Convocation ───────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def convoke(self, request, pk=None):
        """
        Convoquer un ou plusieurs participants.
        Envoie email + SMS + notification in-app selon les flags.
        Crée un ConvocationAttempt par canal utilisé.
        """
        mediation = self.get_object()
        ser = ConvokeParticipantsSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        results = []
        for pid in data['participant_ids']:
            try:
                participant = MediationParticipant.objects.get(id=pid, mediation=mediation)
            except MediationParticipant.DoesNotExist:
                results.append({'participant_id': pid, 'success': False, 'error': 'Introuvable'})
                continue

            now = timezone.now()
            if not participant.convoked_at:
                participant.convoked_at = now
            participant.last_attempt_at = now
            participant.convocation_attempts += 1
            participant.convocation_sent = True
            participant.save()

            channels_sent = []
            if data.get('send_email'):
                if send_convocation_email(participant, mediation):
                    channels_sent.append('EMAIL')
            if data.get('send_sms'):
                if send_convocation_sms(participant, mediation):
                    channels_sent.append('SMS')
            if data.get('send_push'):
                if send_convocation_inapp(participant, mediation):
                    channels_sent.append('PUSH')

            results.append({
                'participant_id': pid,
                'name': participant.display_name,
                'attempts': participant.convocation_attempts,
                'channels': channels_sent,
                'success': bool(channels_sent),
            })

        return Response({
            'message': f'{len(results)} participant(s) traité(s)',
            'results': results,
        })

    @action(detail=False, methods=['get'], url_path='acknowledge/(?P<token>[^/.]+)')
    def acknowledge_convocation(self, request, token=None):
        """
        Endpoint public (lien dans l'email/SMS) que l'employeur appelle pour
        confirmer la réception de sa convocation.
        GET /mediations/sessions/acknowledge/<token>/
        """
        participant = get_object_or_404(MediationParticipant, acknowledgment_token=token)

        if participant.acknowledged_at:
            return Response({
                'message': 'Vous avez déjà confirmé cette convocation.',
                'acknowledged_at': participant.acknowledged_at,
            })

        participant.acknowledged_at = timezone.now()
        participant.acknowledgment_channel = 'EMAIL'  # lien cliqué depuis email/SMS
        participant.save()

        return Response({
            'message': (
                'Votre accusé de réception a bien été enregistré. '
                'Merci de vous présenter à la séance de médiation.'
            ),
            'session_date': participant.mediation.session_date,
            'complaint_number': participant.mediation.complaint.complaint_number,
        })

    @action(detail=True, methods=['post'])
    def manual_acknowledge(self, request, pk=None):
        """
        Un agent DGT confirme manuellement l'accusé de réception
        (remise en main propre, confirmation téléphonique…).
        """
        mediation = self.get_object()
        ser = ManualAcknowledgeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        participant = get_object_or_404(
            MediationParticipant,
            id=ser.validated_data['participant_id'],
            mediation=mediation,
        )
        participant.acknowledged_at = timezone.now()
        participant.acknowledgment_channel = 'MANUAL'
        participant.manually_acknowledged = True
        participant.manually_acknowledged_by = request.user
        participant.save()

        from .notifications import _log_attempt
        _log_attempt(participant, 'MANUAL', 'DELIVERED')

        return Response({
            'message': f'Accusé de réception manuel enregistré pour {participant.display_name}',
            'acknowledged_at': participant.acknowledged_at,
            'acknowledged_by': request.user.get_full_name(),
        })

    @action(detail=True, methods=['post'])
    def relance(self, request, pk=None):
        """
        Relancer manuellement la convocation pour les participants
        n'ayant pas encore accusé réception.
        """
        mediation = self.get_object()
        non_ack = mediation.participants.filter(
            acknowledged_at__isnull=True,
            manually_acknowledged=False,
        )
        if not non_ack.exists():
            return Response({'message': 'Tous les participants ont accusé réception.'})

        results = []
        for participant in non_ack:
            now = timezone.now()
            participant.last_attempt_at = now
            participant.convocation_attempts += 1
            participant.save()

            channels = []
            if send_convocation_email(participant, mediation):
                channels.append('EMAIL')
            if send_convocation_sms(participant, mediation):
                channels.append('SMS')
            if send_convocation_inapp(participant, mediation):
                channels.append('PUSH')

            if participant.convocation_attempts >= MAX_CONVOCATION_ATTEMPTS:
                notify_hierarchy_no_response(mediation)

            results.append({
                'participant': participant.display_name,
                'attempts': participant.convocation_attempts,
                'channels': channels,
                'escalated': participant.convocation_attempts >= MAX_CONVOCATION_ATTEMPTS,
            })

        return Response({'relances': results})

    # ── Non-comparution ───────────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def report_no_show(self, request, pk=None):
        """
        L'inspecteur constate que l'employeur ne s'est pas présenté.
        → Génère le PV de carence
        → Ouvre un PV d'infraction (si demandé)
        → Escalade la plainte
        → Pénalise le score de conformité de l'entreprise
        """
        mediation = self.get_object()
        ser = ReportNoShowSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        mediation.employer_no_show = True
        mediation.no_show_reported_at = timezone.now()
        mediation.no_show_reported_by = request.user
        mediation.status = 'COMPLETED'
        mediation.completed_at = timezone.now()
        mediation.outcome = 'NO_AGREEMENT'
        mediation.outcome_notes = (
            f"Non-comparution de l'employeur constatée le "
            f"{timezone.now().strftime('%d/%m/%Y à %H:%M')} "
            f"par {request.user.get_full_name()}. "
            + data.get('notes', '')
        )
        mediation.pv_carence_generated = True
        mediation.save()

        complaint = mediation.complaint
        prev_status = complaint.status

        if data.get('escalate', True):
            complaint.status = 'ESCALATED'
            complaint.save()
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                from_status=prev_status,
                to_status='ESCALATED',
                changed_by=request.user,
                reason='Non-comparution de l\'employeur à la séance de médiation',
            )

        # Dégrader le score de conformité de l'entreprise
        if complaint.enterprise:
            enterprise = complaint.enterprise
            enterprise.compliance_score = max(0, (enterprise.compliance_score or 100) - 15)
            enterprise.save()

        # Notifier le plaignant
        ComplaintNotification.objects.create(
            complaint=complaint,
            recipient=complaint.complainant,
            message=(
                f"L'employeur ne s'est pas présenté à la séance de médiation "
                f"du {mediation.session_date.strftime('%d/%m/%Y')}. "
                f"Votre dossier est en cours d'escalade vers la hiérarchie."
            )
        )

        # Notifier la hiérarchie
        notify_hierarchy_no_response(mediation)

        return Response({
            'message': 'Non-comparution enregistrée. PV de carence généré. Dossier escaladé.',
            'complaint_status': complaint.status,
            'enterprise_compliance_score': complaint.enterprise.compliance_score if complaint.enterprise else None,
            'pv_carence_generated': True,
        })

    # ── Report / Annulation ───────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def postpone(self, request, pk=None):
        """Reporter la séance à une nouvelle date."""
        mediation = self.get_object()
        ser = PostponeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        old_date = mediation.session_date
        mediation.session_date = ser.validated_data['new_date']
        mediation.status = 'POSTPONED'
        mediation.postpone_count += 1
        mediation.save()

        # Re-convoquer tous les participants avec la nouvelle date
        for participant in mediation.participants.all():
            participant.acknowledged_at = None
            participant.convocation_sent = False
            participant.save()
            send_convocation_email(participant, mediation)
            send_convocation_sms(participant, mediation)
            send_convocation_inapp(participant, mediation)

        return Response({
            'message': f'Séance reportée du {old_date.strftime("%d/%m/%Y")} au {mediation.session_date.strftime("%d/%m/%Y")}.',
            'postpone_count': mediation.postpone_count,
            'participants_renotified': mediation.participants.count(),
        })

    # ── Cycle de vie de la séance ─────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        mediation = self.get_object()
        mediation.status = 'ONGOING'
        mediation.save()
        return Response({'message': 'Séance de médiation démarrée.'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        mediation = self.get_object()
        mediation.status = 'COMPLETED'
        mediation.completed_at = timezone.now()
        mediation.save()

        complaint = mediation.complaint
        if mediation.outcome == 'AGREEMENT':
            complaint.status = 'RESOLVED'
        elif mediation.outcome == 'NO_AGREEMENT':
            complaint.status = 'JUDICIAL'
        complaint.save()

        return Response({'message': 'Séance de médiation terminée.', 'outcome': mediation.outcome})

    # ── Participants ──────────────────────────────────────────────────────────

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        mediation = self.get_object()
        ser = MediationParticipantSerializer(mediation.participants.all(), many=True)
        return Response(ser.data)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        mediation = self.get_object()
        ser = MediationParticipantSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(mediation=mediation)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    # ── PV ────────────────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def generate_minutes(self, request, pk=None):
        mediation = self.get_object()
        ser = GenerateMinutesSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        minutes, created = MediationMinutes.objects.get_or_create(
            mediation=mediation,
            defaults=ser.validated_data,
        )
        if not created:
            for k, v in ser.validated_data.items():
                setattr(minutes, k, v)
            minutes.save()

        return Response({
            'message': 'Procès-verbal généré.',
            'minutes': MediationMinutesSerializer(minutes).data,
        })

    @action(detail=True, methods=['get'])
    def minutes(self, request, pk=None):
        mediation = self.get_object()
        try:
            return Response(MediationMinutesSerializer(mediation.minutes).data)
        except MediationMinutes.DoesNotExist:
            return Response({'error': 'Aucun PV trouvé.'}, status=status.HTTP_404_NOT_FOUND)

    # ── Accord ────────────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def create_agreement(self, request, pk=None):
        mediation = self.get_object()
        ser = CreateAgreementSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        agreement = Agreement.objects.create(mediation=mediation, **ser.validated_data)
        return Response({
            'message': 'Accord créé.',
            'agreement': AgreementSerializer(agreement).data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def agreement(self, request, pk=None):
        mediation = self.get_object()
        try:
            return Response(AgreementSerializer(mediation.agreement).data)
        except Agreement.DoesNotExist:
            return Response({'error': 'Aucun accord trouvé.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def sign_agreement(self, request, pk=None):
        mediation = self.get_object()
        ser = SignAgreementSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        try:
            agreement = mediation.agreement
        except Agreement.DoesNotExist:
            return Response({'error': 'Aucun accord à signer.'}, status=status.HTTP_404_NOT_FOUND)

        role = ser.validated_data['signer_role']
        sig  = ser.validated_data['signature_image']
        if role == 'employee':
            agreement.employee_signature = sig
        elif role == 'employer':
            agreement.employer_signature = sig
        elif role == 'mediator':
            agreement.mediator_signature = sig
        agreement.save()

        if agreement.is_fully_signed() and agreement.status == 'PENDING_SIGNATURE':
            agreement.status = 'SIGNED'
            agreement.signed_at = timezone.now()
            agreement.save()
            mediation.outcome = 'AGREEMENT'
            mediation.save()

        return Response({
            'message': f'Signature {role} enregistrée.',
            'is_fully_signed': agreement.is_fully_signed(),
        })

    # ── Documents ─────────────────────────────────────────────────────────────

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        mediation = self.get_object()
        ser = MediationDocumentSerializer(mediation.documents.all(), many=True)
        return Response(ser.data)

    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        mediation = self.get_object()
        ser = MediationDocumentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(mediation=mediation, uploaded_by=request.user)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    # ── Vues de liste filtrées ────────────────────────────────────────────────

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        qs = self.queryset.filter(
            session_date__gte=timezone.now(),
            status='SCHEDULED',
        ).order_by('session_date')
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def my_mediations(self, request):
        qs = self.queryset.filter(mediator=request.user)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def no_shows(self, request):
        """Liste des médiations avec non-comparution employeur."""
        qs = self.queryset.filter(employer_no_show=True)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def pending_acknowledgment(self, request):
        """Médiations avec des employeurs n'ayant pas encore accusé réception."""
        qs = self.queryset.filter(
            status='SCHEDULED',
            participants__role='EMPLOYER',
            participants__acknowledged_at__isnull=True,
            participants__manually_acknowledged=False,
            participants__convocation_sent=True,
        ).distinct()
        return Response(self.get_serializer(qs, many=True).data)


class MediationParticipantViewSet(viewsets.ModelViewSet):
    queryset = MediationParticipant.objects.select_related(
        'participant', 'manually_acknowledged_by'
    ).prefetch_related('convocation_attempts_log').all()
    serializer_class = MediationParticipantSerializer
    permission_classes = [IsInspecteurOrEmploye]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['mediation', 'role', 'attended', 'convocation_sent']


class AgreementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Agreement.objects.all()
    serializer_class = AgreementSerializer
    permission_classes = [IsInspecteurOrEmploye]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'mediation']

    @action(detail=True, methods=['post'])
    def mark_executed(self, request, pk=None):
        agreement = self.get_object()
        agreement.status = 'EXECUTED'
        agreement.save()
        return Response({'message': 'Accord marqué comme exécuté.'})

    @action(detail=True, methods=['post'])
    def mark_breached(self, request, pk=None):
        agreement = self.get_object()
        agreement.status = 'BREACHED'
        agreement.save()

        ComplaintNotification.objects.create(
            complaint=agreement.mediation.complaint,
            recipient=agreement.mediation.mediator,
            message=f'⚠️ Accord violé — {agreement.mediation.complaint.complaint_number}',
        )
        # Réouvrir la plainte pour procédure judiciaire
        complaint = agreement.mediation.complaint
        complaint.status = 'JUDICIAL'
        complaint.save()

        return Response({'message': 'Accord marqué comme violé. Dossier transmis en procédure judiciaire.'})


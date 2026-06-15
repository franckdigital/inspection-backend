from rest_framework import serializers
from .models import (
    Mediation, MediationParticipant, ConvocationAttempt,
    MediationMinutes, Agreement, MediationDocument
)
from users.serializers import UserDetailSerializer


class ConvocationAttemptSerializer(serializers.ModelSerializer):
    channel_label = serializers.CharField(source='get_channel_display', read_only=True)
    status_label  = serializers.CharField(source='get_status_display',  read_only=True)

    class Meta:
        model = ConvocationAttempt
        fields = [
            'id', 'channel', 'channel_label', 'status', 'status_label',
            'sent_at', 'provider_message_id', 'error_detail',
        ]
        read_only_fields = fields


class MediationParticipantSerializer(serializers.ModelSerializer):
    participant_name       = serializers.SerializerMethodField()
    is_acknowledged        = serializers.BooleanField(read_only=True)
    convocation_attempts_log = ConvocationAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = MediationParticipant
        fields = [
            'id', 'mediation', 'participant', 'participant_name',
            'name', 'email', 'phone', 'role',
            'attended', 'signed', 'signature',
            # convocation
            'convoked_at', 'last_attempt_at', 'convocation_attempts',
            'convocation_sent', 'acknowledgment_token',
            'acknowledged_at', 'acknowledgment_channel',
            'is_acknowledged',
            'manually_acknowledged', 'manually_acknowledged_by',
            # historique
            'convocation_attempts_log',
            'created_at',
        ]
        read_only_fields = (
            'created_at', 'convoked_at', 'last_attempt_at',
            'convocation_attempts', 'convocation_sent',
            'acknowledged_at', 'acknowledgment_channel',
            'acknowledgment_token', 'is_acknowledged',
        )

    def get_participant_name(self, obj):
        return obj.display_name


class MediationSerializer(serializers.ModelSerializer):
    mediator_name      = serializers.SerializerMethodField()
    complaint_number   = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()
    # convocations
    employer_participant_acknowledged = serializers.SerializerMethodField()
    convocation_attempts_count        = serializers.SerializerMethodField()

    class Meta:
        model = Mediation
        fields = [
            'id', 'complaint', 'complaint_number',
            'mediator', 'mediator_name',
            'session_date', 'session_type', 'status',
            'location', 'meeting_link',
            'outcome', 'outcome_notes',
            # non-comparution
            'employer_no_show', 'no_show_reported_at',
            'pv_carence_generated', 'pv_carence_file',
            'postpone_count',
            # computed
            'participants_count',
            'employer_participant_acknowledged',
            'convocation_attempts_count',
            'created_at', 'updated_at', 'completed_at',
        ]
        read_only_fields = (
            'created_at', 'updated_at', 'completed_at',
            'pv_carence_generated', 'pv_carence_file',
            'no_show_reported_at',
        )

    def get_mediator_name(self, obj):
        return obj.mediator.get_full_name() if obj.mediator else None

    def get_complaint_number(self, obj):
        return obj.complaint.complaint_number

    def get_participants_count(self, obj):
        return obj.participants.count()

    def get_employer_participant_acknowledged(self, obj):
        """True si l'employeur a confirmé réception de la convocation."""
        emp = obj.participants.filter(role='EMPLOYER').first()
        return emp.is_acknowledged if emp else None

    def get_convocation_attempts_count(self, obj):
        """Nombre total de tentatives de convocation envers l'employeur."""
        emp = obj.participants.filter(role='EMPLOYER').first()
        return emp.convocation_attempts if emp else 0


class MediationDetailSerializer(serializers.ModelSerializer):
    mediator     = UserDetailSerializer(read_only=True)
    participants = MediationParticipantSerializer(many=True, read_only=True)
    documents_count = serializers.SerializerMethodField()
    no_show_reported_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Mediation
        fields = '__all__'

    def get_documents_count(self, obj):
        return obj.documents.count()

    def get_no_show_reported_by_name(self, obj):
        return obj.no_show_reported_by.get_full_name() if obj.no_show_reported_by else None


# ── Requêtes spéciales ────────────────────────────────────────────────────────

class ConvokeParticipantsSerializer(serializers.Serializer):
    participant_ids = serializers.ListField(child=serializers.IntegerField(), required=True)
    send_email      = serializers.BooleanField(default=True)
    send_sms        = serializers.BooleanField(default=True)
    send_push       = serializers.BooleanField(default=True)


class AcknowledgeConvocationSerializer(serializers.Serializer):
    token = serializers.UUIDField(required=True)


class ManualAcknowledgeSerializer(serializers.Serializer):
    participant_id = serializers.IntegerField(required=True)
    note           = serializers.CharField(required=False, allow_blank=True)


class ReportNoShowSerializer(serializers.Serializer):
    notes              = serializers.CharField(required=False, allow_blank=True)
    open_infraction_pv = serializers.BooleanField(default=True)
    escalate           = serializers.BooleanField(default=True)


class PostponeSerializer(serializers.Serializer):
    new_date = serializers.DateTimeField(required=True)
    reason   = serializers.CharField(required=True)


class MediationMinutesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediationMinutes
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'signed_at')


class GenerateMinutesSerializer(serializers.Serializer):
    opening_statement  = serializers.CharField(required=True)
    employee_statement = serializers.CharField(required=False, allow_blank=True)
    employer_statement = serializers.CharField(required=False, allow_blank=True)
    discussion_summary = serializers.CharField(required=True)
    agreements_reached = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class AgreementSerializer(serializers.ModelSerializer):
    is_fully_signed = serializers.SerializerMethodField()

    class Meta:
        model = Agreement
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'signed_at')

    def get_is_fully_signed(self, obj):
        return obj.is_fully_signed()


class CreateAgreementSerializer(serializers.Serializer):
    agreement_text       = serializers.CharField(required=True)
    terms                = serializers.ListField(child=serializers.CharField(), required=True)
    employee_obligations = serializers.CharField(required=False, allow_blank=True)
    employer_obligations = serializers.CharField(required=False, allow_blank=True)
    compensation_amount  = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    execution_deadline   = serializers.DateField(required=False, allow_null=True)


class SignAgreementSerializer(serializers.Serializer):
    signer_role     = serializers.ChoiceField(choices=['employee', 'employer', 'mediator'], required=True)
    signature_image = serializers.ImageField(required=True)


class MediationDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MediationDocument
        fields = '__all__'
        read_only_fields = ('uploaded_at',)

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None

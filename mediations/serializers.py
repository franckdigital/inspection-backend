from rest_framework import serializers
from .models import (
    Mediation, MediationParticipant, MediationMinutes,
    Agreement, MediationDocument
)
from users.serializers import UserDetailSerializer


class MediationParticipantSerializer(serializers.ModelSerializer):
    participant_name = serializers.SerializerMethodField()

    class Meta:
        model = MediationParticipant
        fields = '__all__'
        read_only_fields = ('created_at',)

    def get_participant_name(self, obj):
        if obj.participant:
            return obj.participant.get_full_name()
        return obj.name


class MediationSerializer(serializers.ModelSerializer):
    mediator_name = serializers.SerializerMethodField()
    complaint_number = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = Mediation
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'completed_at')

    def get_mediator_name(self, obj):
        if obj.mediator:
            return obj.mediator.get_full_name()
        return None

    def get_complaint_number(self, obj):
        return obj.complaint.complaint_number

    def get_participants_count(self, obj):
        return obj.participants.count()


class MediationDetailSerializer(serializers.ModelSerializer):
    mediator = UserDetailSerializer(read_only=True)
    participants = MediationParticipantSerializer(many=True, read_only=True)
    documents_count = serializers.SerializerMethodField()

    class Meta:
        model = Mediation
        fields = '__all__'

    def get_documents_count(self, obj):
        return obj.documents.count()


class ConvokeParticipantsSerializer(serializers.Serializer):
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    send_email = serializers.BooleanField(default=True)
    send_sms = serializers.BooleanField(default=False)


class MediationMinutesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediationMinutes
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'signed_at')


class GenerateMinutesSerializer(serializers.Serializer):
    opening_statement = serializers.CharField(required=True)
    employee_statement = serializers.CharField(required=False, allow_blank=True)
    employer_statement = serializers.CharField(required=False, allow_blank=True)
    discussion_summary = serializers.CharField(required=True)
    agreements_reached = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )


class AgreementSerializer(serializers.ModelSerializer):
    is_fully_signed = serializers.SerializerMethodField()

    class Meta:
        model = Agreement
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'signed_at')

    def get_is_fully_signed(self, obj):
        return obj.is_fully_signed()


class CreateAgreementSerializer(serializers.Serializer):
    agreement_text = serializers.CharField(required=True)
    terms = serializers.ListField(
        child=serializers.CharField(),
        required=True
    )
    employee_obligations = serializers.CharField(required=False, allow_blank=True)
    employer_obligations = serializers.CharField(required=False, allow_blank=True)
    compensation_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    execution_deadline = serializers.DateField(required=False, allow_null=True)


class SignAgreementSerializer(serializers.Serializer):
    signer_role = serializers.ChoiceField(
        choices=['employee', 'employer', 'mediator'],
        required=True
    )
    signature_image = serializers.ImageField(required=True)


class MediationDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MediationDocument
        fields = '__all__'
        read_only_fields = ('uploaded_at',)

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name()
        return None

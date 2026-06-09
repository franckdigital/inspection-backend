from rest_framework import serializers
from .models import (
    DomesticWorker, DomesticEmployer, DomesticContract,
    TimeTracking, MonthlyPayslip, LeaveRequest, VoiceComplaint, OvertimeSession,
    FieldVisit,
)
from decimal import Decimal


class DomesticWorkerSerializer(serializers.ModelSerializer):
    user_name              = serializers.SerializerMethodField()
    user_email             = serializers.SerializerMethodField()
    user_city              = serializers.SerializerMethodField()
    user_phone             = serializers.SerializerMethodField()
    assigned_inspector_name = serializers.SerializerMethodField()
    active_contracts_count  = serializers.SerializerMethodField()

    class Meta:
        model = DomesticWorker
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'assigned_inspector')

    def get_user_name(self, obj):
        return obj.user.get_full_name()

    def get_user_email(self, obj):
        return obj.user.email

    def get_user_city(self, obj):
        return getattr(obj.user, 'city', '') or ''

    def get_user_phone(self, obj):
        phone = getattr(obj.user, 'phone_number', None)
        return str(phone) if phone else ''

    def get_assigned_inspector_name(self, obj):
        if obj.assigned_inspector:
            return obj.assigned_inspector.get_full_name()
        return None

    def get_active_contracts_count(self, obj):
        return obj.contracts.filter(status='ACTIVE').count()


class DomesticEmployerSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = DomesticEmployer
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_user_name(self, obj):
        return obj.user.get_full_name()


class DomesticContractSerializer(serializers.ModelSerializer):
    worker_name     = serializers.SerializerMethodField()
    employer_name   = serializers.SerializerMethodField()
    inspector_name  = serializers.SerializerMethodField()
    inspector_phone = serializers.SerializerMethodField()
    is_fully_signed = serializers.SerializerMethodField()
    worker_city     = serializers.SerializerMethodField()
    employer_city   = serializers.SerializerMethodField()

    class Meta:
        model = DomesticContract
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'signed_at', 'inspector')

    def get_worker_name(self, obj):
        return obj.worker.user.get_full_name()

    def get_employer_name(self, obj):
        return obj.employer.user.get_full_name()

    def get_inspector_name(self, obj):
        if obj.inspector:
            return obj.inspector.get_full_name()
        return None

    def get_inspector_phone(self, obj):
        if obj.inspector and obj.inspector.phone_number:
            return str(obj.inspector.phone_number)
        return None

    def get_is_fully_signed(self, obj):
        return obj.is_fully_signed()

    def get_worker_city(self, obj):
        return getattr(obj.worker.user, 'city', '') or ''

    def get_employer_city(self, obj):
        try:
            return getattr(obj.employer.user, 'city', '') or getattr(obj.employer, 'city', '') or ''
        except Exception:
            return ''


class SignContractSerializer(serializers.Serializer):
    signer_role = serializers.ChoiceField(choices=['worker', 'employer'], required=True)
    signature_image = serializers.ImageField(required=True)


class TimeTrackingSerializer(serializers.ModelSerializer):
    contract_info = serializers.SerializerMethodField()
    worker_name   = serializers.SerializerMethodField()

    class Meta:
        model = TimeTracking
        fields = '__all__'
        read_only_fields = ('created_at', 'hours_worked', 'overtime_hours')

    def get_contract_info(self, obj):
        if obj.contract:
            return {
                'worker':   obj.contract.worker.user.get_full_name(),
                'employer': obj.contract.employer.user.get_full_name(),
            }
        if obj.worker:
            return {'worker': obj.worker.user.get_full_name(), 'employer': None}
        return None

    def get_worker_name(self, obj):
        if obj.worker:
            return obj.worker.user.get_full_name()
        if obj.contract:
            return obj.contract.worker.user.get_full_name()
        return None


class CheckInSerializer(serializers.Serializer):
    contract_id = serializers.IntegerField(required=False, allow_null=True)
    worker_id   = serializers.IntegerField(required=False, allow_null=True)
    latitude    = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    longitude   = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    address     = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if not data.get('contract_id') and not data.get('worker_id'):
            raise serializers.ValidationError('contract_id ou worker_id requis.')
        return data


class CheckOutSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    address = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class MonthlyPayslipSerializer(serializers.ModelSerializer):
    contract_info = serializers.SerializerMethodField()
    worker_name   = serializers.SerializerMethodField()

    class Meta:
        model = MonthlyPayslip
        fields = '__all__'
        read_only_fields = ('generated_at', 'updated_at', 'gross_pay', 'total_deductions', 'net_pay')

    def get_contract_info(self, obj):
        if obj.contract:
            return {
                'worker':   obj.contract.worker.user.get_full_name(),
                'employer': obj.contract.employer.user.get_full_name(),
            }
        if obj.worker:
            return {'worker': obj.worker.user.get_full_name(), 'employer': None}
        return None

    def get_worker_name(self, obj):
        if obj.worker:
            return obj.worker.user.get_full_name()
        if obj.contract:
            return obj.contract.worker.user.get_full_name()
        return None


class GeneratePayslipSerializer(serializers.Serializer):
    contract_id      = serializers.IntegerField(required=False, allow_null=True)
    worker_id        = serializers.IntegerField(required=False, allow_null=True)
    month            = serializers.DateField(required=True)
    base_salary      = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    bonuses          = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    other_deductions = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)

    def validate(self, data):
        if not data.get('contract_id') and not data.get('worker_id'):
            raise serializers.ValidationError('contract_id ou worker_id requis.')
        return data


class LeaveRequestSerializer(serializers.ModelSerializer):
    contract_info = serializers.SerializerMethodField()
    worker_name   = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = '__all__'
        read_only_fields = ('created_at', 'responded_at')

    def get_contract_info(self, obj):
        if obj.contract:
            return {
                'worker':   obj.contract.worker.user.get_full_name(),
                'employer': obj.contract.employer.user.get_full_name(),
            }
        if obj.worker:
            return {'worker': obj.worker.user.get_full_name(), 'employer': None}
        return None

    def get_worker_name(self, obj):
        if obj.worker:
            return obj.worker.user.get_full_name()
        if obj.contract:
            return obj.contract.worker.user.get_full_name()
        return None


class ApproveRejectLeaveSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'], required=True)
    response_comment = serializers.CharField(required=False, allow_blank=True)


class VoiceComplaintSerializer(serializers.ModelSerializer):
    worker_name = serializers.SerializerMethodField()
    worker_employer = serializers.SerializerMethodField()
    worker_commune = serializers.SerializerMethodField()
    inspector_name = serializers.SerializerMethodField()
    assistance_inspector_name = serializers.SerializerMethodField()
    audio_file_url = serializers.SerializerMethodField()
    response_audio_url = serializers.SerializerMethodField()
    duration_display = serializers.SerializerMethodField()

    class Meta:
        model = VoiceComplaint
        fields = '__all__'
        read_only_fields = (
            'case_number', 'created_at', 'updated_at', 'assigned_inspector',
            'transcription_original', 'transcription_french', 'transcription_status',
            'assistance_inspector', 'assistance_responded_at',
        )

    def get_worker_name(self, obj):
        return obj.worker.user.get_full_name()

    def get_worker_employer(self, obj):
        contract = obj.worker.contracts.filter(status='ACTIVE').first()
        if contract:
            return contract.employer.user.get_full_name()
        return None

    def get_worker_commune(self, obj):
        return obj.commune or obj.worker.user.city if hasattr(obj.worker.user, 'city') else ''

    def get_inspector_name(self, obj):
        if obj.assigned_inspector:
            return obj.assigned_inspector.get_full_name()
        return None

    def get_assistance_inspector_name(self, obj):
        if obj.assistance_inspector:
            return obj.assistance_inspector.get_full_name()
        return None

    def get_audio_file_url(self, obj):
        request = self.context.get('request')
        if obj.audio_file and request:
            return request.build_absolute_uri(obj.audio_file.url)
        return None

    def get_response_audio_url(self, obj):
        request = self.context.get('request')
        if obj.inspector_response_audio and request:
            return request.build_absolute_uri(obj.inspector_response_audio.url)
        return None

    def get_duration_display(self, obj):
        s = obj.duration_seconds
        m, sec = divmod(s, 60)
        return f"{m} min {sec:02d} sec" if m else f"{sec} sec"


class VoiceComplaintCreateSerializer(serializers.Serializer):
    audio_file = serializers.FileField()
    duration_seconds = serializers.IntegerField(default=0)
    selected_language = serializers.ChoiceField(
        choices=[c[0] for c in VoiceComplaint.LANGUAGE_CHOICES], required=False, allow_blank=True
    )
    detected_language = serializers.ChoiceField(
        choices=[c[0] for c in VoiceComplaint.LANGUAGE_CHOICES], required=False, allow_blank=True
    )
    language_confidence = serializers.FloatField(default=0.0)
    commune = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)


class OvertimeSessionSerializer(serializers.ModelSerializer):
    duration_display = serializers.SerializerMethodField()

    class Meta:
        model = OvertimeSession
        fields = '__all__'
        read_only_fields = ('tracking', 'end_time', 'duration_minutes', 'is_active', 'created_at')

    def get_duration_display(self, obj):
        if obj.duration_minutes:
            h, m = divmod(obj.duration_minutes, 60)
            return f"{h}h{m:02d}" if h else f"{m} min"
        return 'En cours'


class InspectorRespondSerializer(serializers.Serializer):
    response_text = serializers.CharField(required=False, allow_blank=True)
    response_audio = serializers.FileField(required=False)


class FieldVisitSerializer(serializers.ModelSerializer):
    inspector_name   = serializers.SerializerMethodField()
    worker_name      = serializers.SerializerMethodField()
    employer_name    = serializers.SerializerMethodField()
    effective_worker_id = serializers.SerializerMethodField()
    status_display   = serializers.SerializerMethodField()

    class Meta:
        model  = FieldVisit
        fields = '__all__'
        read_only_fields = ('inspector', 'actual_date', 'created_at', 'updated_at')

    def get_inspector_name(self, obj):
        return obj.inspector.get_full_name()

    def _effective_worker(self, obj):
        if obj.worker:
            return obj.worker
        if obj.contract:
            return obj.contract.worker
        return None

    def get_worker_name(self, obj):
        w = self._effective_worker(obj)
        return w.user.get_full_name() if w else None

    def get_employer_name(self, obj):
        return obj.contract.employer.user.get_full_name() if obj.contract else None

    def get_effective_worker_id(self, obj):
        w = self._effective_worker(obj)
        return w.id if w else None

    def get_status_display(self, obj):
        return obj.get_status_display()


class RecordGPSSerializer(serializers.Serializer):
    latitude  = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    address   = serializers.CharField(required=False, allow_blank=True)
    status    = serializers.ChoiceField(
        choices=['IN_PROGRESS', 'COMPLETED'], default='IN_PROGRESS'
    )

from rest_framework import serializers
from .models import JudicialProcedure, CourtDocument, Hearing, JudicialDecision


class JudicialProcedureSerializer(serializers.ModelSerializer):
    plaintiff_name = serializers.SerializerMethodField()
    complaint_number = serializers.SerializerMethodField()
    case_officer_name = serializers.SerializerMethodField()
    hearings_count = serializers.SerializerMethodField()

    class Meta:
        model = JudicialProcedure
        fields = '__all__'
        read_only_fields = ('procedure_number', 'created_at', 'updated_at')

    def get_plaintiff_name(self, obj):
        return obj.plaintiff.get_full_name() if obj.plaintiff else None

    def get_complaint_number(self, obj):
        return obj.complaint.complaint_number

    def get_case_officer_name(self, obj):
        return obj.case_officer.get_full_name() if obj.case_officer else None

    def get_hearings_count(self, obj):
        return obj.hearings.count()


class CourtDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CourtDocument
        fields = '__all__'
        read_only_fields = ('upload_date',)

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None


class HearingSerializer(serializers.ModelSerializer):
    procedure_number = serializers.SerializerMethodField()

    class Meta:
        model = Hearing
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_procedure_number(self, obj):
        return obj.procedure.procedure_number


class JudicialDecisionSerializer(serializers.ModelSerializer):
    procedure_number = serializers.SerializerMethodField()
    total_awarded = serializers.SerializerMethodField()

    class Meta:
        model = JudicialDecision
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_procedure_number(self, obj):
        return obj.procedure.procedure_number

    def get_total_awarded(self, obj):
        total = 0
        if obj.awarded_amount:
            total += float(obj.awarded_amount)
        if obj.damages:
            total += float(obj.damages)
        return total


class TransmitToCourtSerializer(serializers.Serializer):
    court_name = serializers.CharField(required=True)
    submission_date = serializers.DateField(required=True)
    court_reference = serializers.CharField(required=False, allow_blank=True)

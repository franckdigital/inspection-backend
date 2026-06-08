from rest_framework import serializers
from .models import WorkflowApproval, Escalation, Delegation, ReassignmentHistory
from users.serializers import UserDetailSerializer
from complaints.serializers import ComplaintSerializer


class WorkflowApprovalSerializer(serializers.ModelSerializer):
    approver_name = serializers.SerializerMethodField()
    complaint_number = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowApproval
        fields = '__all__'
        read_only_fields = ('created_at', 'approved_at')

    def get_approver_name(self, obj):
        return obj.approver.get_full_name()

    def get_complaint_number(self, obj):
        return obj.complaint.complaint_number


class ApproveRejectSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'], required=True)


class EscalationSerializer(serializers.ModelSerializer):
    from_user_name = serializers.SerializerMethodField()
    to_user_name = serializers.SerializerMethodField()
    complaint_number = serializers.SerializerMethodField()

    class Meta:
        model = Escalation
        fields = '__all__'
        read_only_fields = ('escalated_at', 'resolved_at')

    def get_from_user_name(self, obj):
        return obj.from_user.get_full_name()

    def get_to_user_name(self, obj):
        return obj.to_user.get_full_name()

    def get_complaint_number(self, obj):
        return obj.complaint.complaint_number


class EscalateComplaintSerializer(serializers.Serializer):
    to_user_id = serializers.IntegerField(required=True)
    reason = serializers.ChoiceField(
        choices=['DELAY', 'COMPLEXITY', 'CONFLICT', 'MANUAL', 'OTHER'],
        required=True
    )
    description = serializers.CharField(required=True)


class DelegationSerializer(serializers.ModelSerializer):
    from_user_name = serializers.SerializerMethodField()
    to_user_name = serializers.SerializerMethodField()
    is_valid_now = serializers.SerializerMethodField()

    class Meta:
        model = Delegation
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_from_user_name(self, obj):
        return obj.from_user.get_full_name()

    def get_to_user_name(self, obj):
        return obj.to_user.get_full_name()

    def get_is_valid_now(self, obj):
        return obj.is_valid()


class ReassignmentHistorySerializer(serializers.ModelSerializer):
    from_inspector_name = serializers.SerializerMethodField()
    to_inspector_name = serializers.SerializerMethodField()
    reassigned_by_name = serializers.SerializerMethodField()
    complaint_number = serializers.SerializerMethodField()

    class Meta:
        model = ReassignmentHistory
        fields = '__all__'
        read_only_fields = ('reassigned_at',)

    def get_from_inspector_name(self, obj):
        return obj.from_inspector.get_full_name()

    def get_to_inspector_name(self, obj):
        return obj.to_inspector.get_full_name()

    def get_reassigned_by_name(self, obj):
        return obj.reassigned_by.get_full_name()

    def get_complaint_number(self, obj):
        return obj.complaint.complaint_number


class ReassignComplaintSerializer(serializers.Serializer):
    to_inspector_id = serializers.IntegerField(required=True)
    reason = serializers.CharField(required=True)

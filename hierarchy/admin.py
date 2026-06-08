from django.contrib import admin
from .models import WorkflowApproval, Escalation, Delegation, ReassignmentHistory


@admin.register(WorkflowApproval)
class WorkflowApprovalAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'approver', 'level', 'status', 'created_at', 'approved_at')
    list_filter = ('status', 'level', 'created_at')
    search_fields = ('complaint__complaint_number', 'approver__email', 'comment')
    readonly_fields = ('created_at', 'approved_at')
    raw_id_fields = ('complaint', 'approver')


@admin.register(Escalation)
class EscalationAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'from_user', 'to_user', 'reason', 'is_resolved', 'escalated_at')
    list_filter = ('reason', 'is_resolved', 'escalated_at')
    search_fields = ('complaint__complaint_number', 'from_user__email', 'to_user__email')
    readonly_fields = ('escalated_at', 'resolved_at')
    raw_id_fields = ('complaint', 'from_user', 'to_user')


@admin.register(Delegation)
class DelegationAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('from_user__email', 'to_user__email', 'reason')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('from_user', 'to_user')


@admin.register(ReassignmentHistory)
class ReassignmentHistoryAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'from_inspector', 'to_inspector', 'reassigned_by', 'reassigned_at')
    list_filter = ('reassigned_at',)
    search_fields = ('complaint__complaint_number', 'from_inspector__email', 'to_inspector__email')
    readonly_fields = ('reassigned_at',)
    raw_id_fields = ('complaint', 'from_inspector', 'to_inspector', 'reassigned_by')


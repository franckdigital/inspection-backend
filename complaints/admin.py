from django.contrib import admin
from .models import Complaint, ComplaintDocument, ComplaintComment, ComplaintStatusHistory, ComplaintNotification


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('complaint_number', 'complainant', 'complaint_type', 'status', 'priority', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'complaint_type', 'created_at')
    search_fields = ('complaint_number', 'subject', 'complainant__email', 'employer_name')
    readonly_fields = ('complaint_number', 'created_at', 'updated_at')
    raw_id_fields = ('complainant', 'enterprise', 'assigned_to', 'inspection_zone')


@admin.register(ComplaintDocument)
class ComplaintDocumentAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'document_type', 'title', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('title', 'complaint__complaint_number')


@admin.register(ComplaintComment)
class ComplaintCommentAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'author', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('complaint__complaint_number', 'author__email', 'comment')


@admin.register(ComplaintStatusHistory)
class ComplaintStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'from_status', 'to_status', 'changed_by', 'created_at')
    list_filter = ('from_status', 'to_status', 'created_at')
    search_fields = ('complaint__complaint_number',)


@admin.register(ComplaintNotification)
class ComplaintNotificationAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'recipient', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('complaint__complaint_number', 'recipient__email')

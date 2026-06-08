from django.contrib import admin
from .models import EmailTemplate, EmailLog, SMSTemplate, SMSLog, NotificationQueue


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'subject', 'is_active', 'updated_at')
    list_filter = ('template_type', 'is_active')
    search_fields = ('name', 'subject')


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'subject', 'status', 'sent_at', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('recipient_email', 'subject')
    readonly_fields = ('created_at', 'sent_at', 'opened_at', 'clicked_at')


@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'content_preview', 'is_active', 'updated_at')
    list_filter = ('template_type', 'is_active')
    search_fields = ('name', 'content')

    def content_preview(self, obj):
        return obj.content[:50]


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_phone', 'content_preview', 'status', 'sent_at', 'cost')
    list_filter = ('status', 'created_at')
    search_fields = ('recipient_phone', 'content')
    readonly_fields = ('created_at', 'sent_at', 'delivered_at')

    def content_preview(self, obj):
        return obj.content[:30]


@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'template_name', 'recipient_email', 'priority', 'processed', 'created_at')
    list_filter = ('notification_type', 'processed', 'priority')
    search_fields = ('recipient_email', 'recipient_phone', 'template_name')
    readonly_fields = ('created_at', 'processed_at')

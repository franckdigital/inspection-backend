from django.contrib import admin
from .models import (
    Mediation, MediationParticipant, MediationMinutes,
    Agreement, MediationDocument
)


@admin.register(Mediation)
class MediationAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'mediator', 'session_date', 'session_type', 'status', 'outcome')
    list_filter = ('status', 'session_type', 'outcome', 'session_date')
    search_fields = ('complaint__complaint_number', 'mediator__email', 'location')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    raw_id_fields = ('complaint', 'mediator')


@admin.register(MediationParticipant)
class MediationParticipantAdmin(admin.ModelAdmin):
    list_display = ('mediation', 'participant', 'name', 'role', 'attended', 'signed')
    list_filter = ('role', 'attended', 'signed', 'convocation_sent')
    search_fields = ('name', 'email', 'phone', 'participant__email')
    readonly_fields = ('created_at', 'convoked_at')
    raw_id_fields = ('mediation', 'participant')


@admin.register(MediationMinutes)
class MediationMinutesAdmin(admin.ModelAdmin):
    list_display = ('mediation', 'signed_by_all', 'signed_at', 'created_at')
    list_filter = ('signed_by_all', 'signed_at')
    search_fields = ('mediation__complaint__complaint_number',)
    readonly_fields = ('created_at', 'updated_at', 'signed_at')
    raw_id_fields = ('mediation',)


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ('mediation', 'status', 'compensation_amount', 'execution_deadline', 'signed_at')
    list_filter = ('status', 'signed_at', 'execution_deadline')
    search_fields = ('mediation__complaint__complaint_number', 'agreement_text')
    readonly_fields = ('created_at', 'updated_at', 'signed_at')
    raw_id_fields = ('mediation',)


@admin.register(MediationDocument)
class MediationDocumentAdmin(admin.ModelAdmin):
    list_display = ('mediation', 'document_type', 'title', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('title', 'mediation__complaint__complaint_number')
    readonly_fields = ('uploaded_at',)
    raw_id_fields = ('mediation', 'uploaded_by')

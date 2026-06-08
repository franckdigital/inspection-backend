from django.contrib import admin
from .models import JudicialProcedure, CourtDocument, Hearing, JudicialDecision


@admin.register(JudicialProcedure)
class JudicialProcedureAdmin(admin.ModelAdmin):
    list_display = ('procedure_number', 'complaint', 'procedure_type', 'status', 'court_name', 'filed_date')
    list_filter = ('status', 'procedure_type', 'filed_date')
    search_fields = ('procedure_number', 'complaint__complaint_number', 'court_name', 'defendant_name')
    readonly_fields = ('procedure_number', 'created_at', 'updated_at')
    raw_id_fields = ('complaint', 'plaintiff', 'case_officer')
    fieldsets = (
        ('Informations générales', {
            'fields': ('procedure_number', 'complaint', 'procedure_type', 'status')
        }),
        ('Parties', {
            'fields': ('plaintiff', 'defendant_name', 'defendant_representative')
        }),
        ('Tribunal', {
            'fields': ('court_name', 'court_reference', 'judge_name', 'filed_date', 'submission_date')
        }),
        ('Gestion', {
            'fields': ('case_officer',)
        }),
        ('Détails', {
            'fields': ('summary', 'legal_grounds', 'claims', 'claimed_amount')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CourtDocument)
class CourtDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'procedure', 'document_type', 'uploaded_by', 'upload_date')
    list_filter = ('document_type', 'upload_date')
    search_fields = ('title', 'procedure__procedure_number', 'description')
    readonly_fields = ('upload_date',)
    raw_id_fields = ('procedure', 'uploaded_by')


@admin.register(Hearing)
class HearingAdmin(admin.ModelAdmin):
    list_display = ('procedure', 'hearing_type', 'status', 'scheduled_date', 'location')
    list_filter = ('status', 'hearing_type', 'scheduled_date')
    search_fields = ('procedure__procedure_number', 'location', 'judge')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('procedure',)


@admin.register(JudicialDecision)
class JudicialDecisionAdmin(admin.ModelAdmin):
    list_display = ('procedure', 'decision_type', 'outcome', 'decision_date', 'is_final')
    list_filter = ('decision_type', 'outcome', 'is_final', 'decision_date')
    search_fields = ('procedure__procedure_number', 'summary')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('procedure',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('procedure', 'decision_type', 'outcome', 'decision_date', 'notification_date')
        }),
        ('Contenu', {
            'fields': ('summary', 'full_text')
        }),
        ('Montants', {
            'fields': ('awarded_amount', 'damages', 'legal_costs')
        }),
        ('Exécution', {
            'fields': ('is_enforceable', 'is_final', 'appeal_deadline', 'decision_file')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

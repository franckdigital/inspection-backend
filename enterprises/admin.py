from django.contrib import admin
from .models import Enterprise, EnterpriseBranch, EnterpriseDocument, EnterpriseHistory


@admin.register(Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ('name', 'rccm', 'nif', 'sector', 'city', 'employee_count', 'compliance_score', 'risk_level', 'is_active')
    list_filter = ('sector', 'risk_level', 'is_active', 'is_verified', 'city')
    search_fields = ('name', 'rccm', 'nif', 'email')
    readonly_fields = ('compliance_score', 'risk_level', 'created_at', 'updated_at')
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'legal_form', 'sector', 'description')
        }),
        ('Identifiants officiels', {
            'fields': ('rccm', 'cc', 'nif', 'cnps_number')
        }),
        ('Coordonnées', {
            'fields': ('headquarters_address', 'city', 'region', 'country', 'latitude', 'longitude', 'phone_number', 'email', 'website')
        }),
        ('Informations opérationnelles', {
            'fields': ('employee_count', 'founding_date', 'inspection_zone')
        }),
        ('Scoring et risques', {
            'fields': ('compliance_score', 'risk_level')
        }),
        ('Statut', {
            'fields': ('is_active', 'is_verified')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(EnterpriseBranch)
class EnterpriseBranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'enterprise', 'city', 'employee_count', 'manager_name', 'is_active')
    list_filter = ('city', 'is_active')
    search_fields = ('name', 'enterprise__name', 'city', 'manager_name')


@admin.register(EnterpriseDocument)
class EnterpriseDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'enterprise', 'document_type', 'issue_date', 'expiry_date', 'is_verified')
    list_filter = ('document_type', 'is_verified', 'issue_date')
    search_fields = ('title', 'enterprise__name')
    readonly_fields = ('uploaded_at', 'updated_at')


@admin.register(EnterpriseHistory)
class EnterpriseHistoryAdmin(admin.ModelAdmin):
    list_display = ('enterprise', 'event_type', 'performed_by', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('enterprise__name', 'description')
    readonly_fields = ('created_at',)

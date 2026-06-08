from django.contrib import admin
from .models import Dashboard, Report, KPI, DataExport


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_public', 'created_by', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('created_by',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'status', 'is_scheduled', 'created_by', 'created_at')
    list_filter = ('report_type', 'status', 'is_scheduled', 'created_at')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('created_by',)


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'current_value', 'target_value', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('code', 'name')


@admin.register(DataExport)
class DataExportAdmin(admin.ModelAdmin):
    list_display = ('title', 'export_format', 'status', 'rows_count', 'requested_by', 'created_at')
    list_filter = ('export_format', 'status', 'created_at')
    search_fields = ('title', 'model_name')
    readonly_fields = ('created_at', 'completed_at')
    raw_id_fields = ('requested_by',)

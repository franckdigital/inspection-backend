from django.contrib import admin
from .models import DailyStatistics, MonthlyReport


@admin.register(DailyStatistics)
class DailyStatisticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'complaints_new', 'complaints_resolved', 'resolution_rate', 'calculated_at')
    list_filter = ('date',)
    readonly_fields = ('calculated_at',)


@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ('month', 'total_complaints', 'total_inspections', 'resolution_rate', 'generated_at')
    list_filter = ('month',)
    readonly_fields = ('generated_at',)

from django.contrib import admin
from .models import InspectionZone, InspectionRecord


@admin.register(InspectionZone)
class InspectionZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'region', 'city', 'head_inspector', 'is_active')
    list_filter = ('region', 'is_active')
    search_fields = ('name', 'code', 'city')
    raw_id_fields = ('head_inspector',)


@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    list_display = ('enterprise', 'inspector', 'inspection_type', 'scheduled_date', 'result', 'is_completed')
    list_filter = ('inspection_type', 'result', 'is_completed', 'scheduled_date')
    search_fields = ('enterprise__name', 'inspector__email')
    raw_id_fields = ('enterprise', 'inspector')

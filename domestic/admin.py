from django.contrib import admin
from .models import (
    DomesticWorker, DomesticEmployer, DomesticContract,
    TimeTracking, MonthlyPayslip, LeaveRequest
)


@admin.register(DomesticWorker)
class DomesticWorkerAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'years_experience', 'is_available')
    list_filter = ('specialization', 'is_available')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)


@admin.register(DomesticEmployer)
class DomesticEmployerAdmin(admin.ModelAdmin):
    list_display = ('user', 'employer_type', 'household_size', 'city')
    list_filter = ('employer_type', 'has_children', 'has_pets')
    search_fields = ('user__email', 'city', 'address')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)


@admin.register(DomesticContract)
class DomesticContractAdmin(admin.ModelAdmin):
    list_display = ('worker', 'employer', 'status', 'start_date', 'salary', 'signed_at')
    list_filter = ('status', 'payment_frequency', 'start_date')
    search_fields = ('worker__user__email', 'employer__user__email')
    readonly_fields = ('created_at', 'updated_at', 'signed_at')
    raw_id_fields = ('worker', 'employer')


@admin.register(TimeTracking)
class TimeTrackingAdmin(admin.ModelAdmin):
    list_display = ('contract', 'date', 'check_in_time', 'check_out_time', 'hours_worked', 'overtime_hours', 'is_validated')
    list_filter = ('is_validated', 'date')
    search_fields = ('contract__worker__user__email',)
    readonly_fields = ('created_at', 'hours_worked', 'overtime_hours')
    raw_id_fields = ('contract',)


@admin.register(MonthlyPayslip)
class MonthlyPayslipAdmin(admin.ModelAdmin):
    list_display = ('contract', 'month', 'status', 'gross_pay', 'net_pay', 'payment_date')
    list_filter = ('status', 'month', 'payment_method')
    search_fields = ('contract__worker__user__email',)
    readonly_fields = ('generated_at', 'updated_at', 'gross_pay', 'total_deductions', 'net_pay')
    raw_id_fields = ('contract',)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('contract', 'leave_type', 'status', 'start_date', 'end_date', 'days_count')
    list_filter = ('leave_type', 'status', 'start_date')
    search_fields = ('contract__worker__user__email', 'reason')
    readonly_fields = ('created_at', 'responded_at')
    raw_id_fields = ('contract',)

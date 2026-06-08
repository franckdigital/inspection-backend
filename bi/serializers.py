from rest_framework import serializers
from .models import Dashboard, Report, KPI, DataExport


class DashboardSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Dashboard
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class ReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class KPISerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = KPI
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_status(self, obj):
        if not obj.current_value or not obj.target_value:
            return 'UNKNOWN'

        if obj.current_value >= obj.target_value:
            return 'SUCCESS'
        elif obj.warning_threshold and obj.current_value >= obj.warning_threshold:
            return 'WARNING'
        else:
            return 'CRITICAL'


class DataExportSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)

    class Meta:
        model = DataExport
        fields = '__all__'
        read_only_fields = ('created_at', 'completed_at')

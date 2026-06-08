from rest_framework import serializers
from .models import Enterprise, EnterpriseBranch, EnterpriseDocument, EnterpriseHistory


class EnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = '__all__'
        read_only_fields = ('compliance_score', 'risk_level', 'created_at', 'updated_at')


class EnterpriseDetailSerializer(serializers.ModelSerializer):
    branches_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    total_employees = serializers.SerializerMethodField()

    class Meta:
        model = Enterprise
        fields = '__all__'

    def get_branches_count(self, obj):
        return obj.branches.count()

    def get_documents_count(self, obj):
        return obj.documents.count()

    def get_total_employees(self, obj):
        branch_employees = sum(branch.employee_count for branch in obj.branches.all())
        return obj.employee_count + branch_employees


class EnterpriseBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnterpriseBranch
        fields = '__all__'


class EnterpriseDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = EnterpriseDocument
        fields = '__all__'

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class EnterpriseHistorySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = EnterpriseHistory
        fields = '__all__'

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return obj.performed_by.get_full_name()
        return None

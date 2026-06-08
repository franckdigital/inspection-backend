from rest_framework import serializers
from .models import DocumentCategory, Document, DocumentVersion, DocumentAccess, Archive


class DocumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = '__all__'


class DocumentVersionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = DocumentVersion
        fields = '__all__'
        read_only_fields = ('created_at',)


class DocumentSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    versions_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'file_size', 'file_type')

    def get_versions_count(self, obj):
        return obj.versions.count()


class DocumentAccessSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)

    class Meta:
        model = DocumentAccess
        fields = '__all__'
        read_only_fields = ('created_at',)


class ArchiveSerializer(serializers.ModelSerializer):
    usage_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Archive
        fields = '__all__'
        read_only_fields = ('created_at',)

    def get_usage_percentage(self, obj):
        if obj.capacity_gb:
            return (obj.used_space_gb / obj.capacity_gb) * 100
        return 0

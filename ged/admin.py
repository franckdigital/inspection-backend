from django.contrib import admin
from .models import DocumentCategory, Document, DocumentVersion, DocumentAccess, Archive


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'retention_years', 'is_archivable')
    list_filter = ('is_archivable',)
    search_fields = ('name', 'code')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'title', 'category', 'status', 'is_confidential', 'created_by', 'created_at')
    list_filter = ('status', 'category', 'is_confidential', 'created_at')
    search_fields = ('reference_number', 'title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'file_size', 'file_type')
    raw_id_fields = ('created_by', 'related_complaint', 'related_enterprise')


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document', 'version_number', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('document__reference_number', 'change_description')
    readonly_fields = ('created_at',)
    raw_id_fields = ('document', 'created_by')


@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('document__reference_number', 'user__email')
    readonly_fields = ('created_at',)
    raw_id_fields = ('document', 'user')


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = ('name', 'archive_type', 'used_space_gb', 'capacity_gb', 'is_active')
    list_filter = ('archive_type', 'is_active')
    search_fields = ('name', 'location')

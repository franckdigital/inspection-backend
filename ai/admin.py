from django.contrib import admin
from .models import ChatConversation, ChatMessage, DocumentAnalysis, ComplaintSimilarity, RiskPrediction, AbuseDetection


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'started_at', 'is_active')
    list_filter = ('is_active', 'started_at')
    search_fields = ('user__email', 'session_id')
    raw_id_fields = ('user',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'content_preview', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content',)
    raw_id_fields = ('conversation',)

    def content_preview(self, obj):
        return obj.content[:50]


@admin.register(DocumentAnalysis)
class DocumentAnalysisAdmin(admin.ModelAdmin):
    list_display = ('uploaded_by', 'document_type', 'status', 'ocr_confidence', 'created_at')
    list_filter = ('status', 'document_type', 'created_at')
    search_fields = ('extracted_text', 'ai_summary')
    raw_id_fields = ('uploaded_by',)


@admin.register(ComplaintSimilarity)
class ComplaintSimilarityAdmin(admin.ModelAdmin):
    list_display = ('complaint1', 'complaint2', 'similarity_score', 'type_match', 'employer_match')
    list_filter = ('type_match', 'employer_match')
    raw_id_fields = ('complaint1', 'complaint2')


@admin.register(RiskPrediction)
class RiskPredictionAdmin(admin.ModelAdmin):
    list_display = ('enterprise', 'risk_type', 'risk_level', 'probability', 'is_active')
    list_filter = ('risk_type', 'risk_level', 'is_active')
    search_fields = ('enterprise__name',)
    raw_id_fields = ('enterprise',)


@admin.register(AbuseDetection)
class AbuseDetectionAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'abuse_type', 'detection_score', 'urgency_level', 'authorities_notified')
    list_filter = ('abuse_type', 'urgency_level', 'authorities_notified')
    search_fields = ('complaint__complaint_number',)
    raw_id_fields = ('complaint',)

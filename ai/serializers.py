from rest_framework import serializers
from .models import ChatConversation, ChatMessage, DocumentAnalysis, ComplaintSimilarity, RiskPrediction, AbuseDetection


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ('created_at',)


class ChatConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    messages_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = '__all__'
        read_only_fields = ('started_at', 'ended_at')

    def get_messages_count(self, obj):
        return obj.messages.count()


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
    session_id = serializers.CharField(required=False, allow_blank=True)


class DocumentAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAnalysis
        fields = '__all__'
        read_only_fields = ('created_at', 'completed_at', 'extracted_text', 'ai_summary')


class ComplaintSimilaritySerializer(serializers.ModelSerializer):
    complaint1_number = serializers.CharField(source='complaint1.complaint_number', read_only=True)
    complaint2_number = serializers.CharField(source='complaint2.complaint_number', read_only=True)

    class Meta:
        model = ComplaintSimilarity
        fields = '__all__'
        read_only_fields = ('calculated_at',)


class RiskPredictionSerializer(serializers.ModelSerializer):
    enterprise_name = serializers.CharField(source='enterprise.name', read_only=True)

    class Meta:
        model = RiskPrediction
        fields = '__all__'
        read_only_fields = ('predicted_at',)


class AbuseDetectionSerializer(serializers.ModelSerializer):
    complaint_number = serializers.CharField(source='complaint.complaint_number', read_only=True)

    class Meta:
        model = AbuseDetection
        fields = '__all__'
        read_only_fields = ('detected_at', 'notified_at')

from rest_framework import serializers
from .models import (
    NewsArticle, FAQ, ResourceDocument, Testimonial,
    Campaign, PressRelease, PressAttachment, ContactMessage,
    InspectionOffice
)


class NewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = '__all__'
        read_only_fields = ('slug', 'views', 'created_at', 'updated_at')


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class ResourceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceDocument
        fields = '__all__'
        read_only_fields = ('file_size', 'downloads', 'created_at', 'updated_at')


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = '__all__'
        read_only_fields = ('is_approved', 'created_at', 'updated_at')


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class PressAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PressAttachment
        fields = ['id', 'file', 'title', 'created_at']


class PressReleaseSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = PressRelease
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_attachments(self, obj):
        return [attachment.file.url for attachment in obj.attachments.all()]


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']


class InspectionOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionOffice
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class PublicStatsSerializer(serializers.Serializer):
    """Statistiques publiques"""
    total_workers = serializers.IntegerField()
    total_enterprises = serializers.IntegerField()
    total_complaints = serializers.IntegerField()
    total_inspections = serializers.IntegerField()
    total_mediations = serializers.IntegerField()
    complaints_resolved = serializers.IntegerField()
    satisfaction_rate = serializers.FloatField()

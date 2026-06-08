from rest_framework import serializers
from .models import EmailTemplate, EmailLog, SMSTemplate, SMSLog, NotificationQueue


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class EmailLogSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template_used.name', read_only=True, allow_null=True)

    class Meta:
        model = EmailLog
        fields = '__all__'
        read_only_fields = ('created_at', 'sent_at', 'opened_at', 'clicked_at')


class SMSTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSTemplate
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class SMSLogSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template_used.name', read_only=True, allow_null=True)

    class Meta:
        model = SMSLog
        fields = '__all__'
        read_only_fields = ('created_at', 'sent_at', 'delivered_at')


class SendEmailSerializer(serializers.Serializer):
    to_email = serializers.EmailField(required=True)
    subject = serializers.CharField(required=True, max_length=255)
    html_content = serializers.CharField(required=True)
    text_content = serializers.CharField(required=False, allow_blank=True)


class SendTemplateEmailSerializer(serializers.Serializer):
    to_email = serializers.EmailField(required=True)
    template_name = serializers.CharField(required=True)
    context = serializers.JSONField(required=True)


class SendSMSSerializer(serializers.Serializer):
    to_phone = serializers.CharField(required=True, max_length=20)
    message = serializers.CharField(required=True, max_length=160)


class SendTemplateSMSSerializer(serializers.Serializer):
    to_phone = serializers.CharField(required=True, max_length=20)
    template_name = serializers.CharField(required=True)
    context = serializers.JSONField(required=True)

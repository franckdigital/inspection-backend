from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import EmailTemplate, EmailLog, SMSTemplate, SMSLog
from .serializers import (
    EmailTemplateSerializer, EmailLogSerializer, SMSTemplateSerializer, SMSLogSerializer,
    SendEmailSerializer, SendTemplateEmailSerializer, SendSMSSerializer, SendTemplateSMSSerializer
)
from .services import EmailService, SMSService
from core.permissions import IsAdmin, IsInspecteur


class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAdmin]


class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmailLog.objects.all()
    serializer_class = EmailLogSerializer
    permission_classes = [IsInspecteur]

    @action(detail=False, methods=['post'])
    def send(self, request):
        """Envoyer un email directement"""
        serializer = SendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = EmailService.send_email(
            to_email=serializer.validated_data['to_email'],
            subject=serializer.validated_data['subject'],
            html_content=serializer.validated_data['html_content'],
            text_content=serializer.validated_data.get('text_content', '')
        )

        return Response(result)

    @action(detail=False, methods=['post'])
    def send_template(self, request):
        """Envoyer un email depuis un template"""
        serializer = SendTemplateEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = EmailService.send_template_email(
            to_email=serializer.validated_data['to_email'],
            template_name=serializer.validated_data['template_name'],
            context=serializer.validated_data['context']
        )

        return Response(result)


class SMSTemplateViewSet(viewsets.ModelViewSet):
    queryset = SMSTemplate.objects.all()
    serializer_class = SMSTemplateSerializer
    permission_classes = [IsAdmin]


class SMSLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SMSLog.objects.all()
    serializer_class = SMSLogSerializer
    permission_classes = [IsInspecteur]

    @action(detail=False, methods=['post'])
    def send(self, request):
        """Envoyer un SMS directement"""
        serializer = SendSMSSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = SMSService.send_sms(
            to_phone=serializer.validated_data['to_phone'],
            message=serializer.validated_data['message']
        )

        return Response(result)

    @action(detail=False, methods=['post'])
    def send_template(self, request):
        """Envoyer un SMS depuis un template"""
        serializer = SendTemplateSMSSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = SMSService.send_template_sms(
            to_phone=serializer.validated_data['to_phone'],
            template_name=serializer.validated_data['template_name'],
            context=serializer.validated_data['context']
        )

        return Response(result)

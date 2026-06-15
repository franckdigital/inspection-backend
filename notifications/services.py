"""Services de notification - Email et SMS"""

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from .models import EmailLog, SMSLog, EmailTemplate, SMSTemplate


class EmailService:
    """Service d'envoi d'emails"""

    @staticmethod
    def send_email(to_email, subject, html_content, text_content='', template_name=None):
        """
        Envoie un email

        En production, utiliser un service comme SendGrid, Mailgun, ou AWS SES
        """
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content or html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email]
            )

            if html_content:
                msg.attach_alternative(html_content, "text/html")

            # Envoyer réellement si EMAIL_HOST_USER est configuré
            if settings.EMAIL_HOST_USER:
                msg.send()

            template_obj = None
            if template_name:
                template_obj = EmailTemplate.objects.filter(name=template_name).first()

            EmailLog.objects.create(
                recipient_email=to_email,
                subject=subject,
                body_html=html_content,
                body_text=text_content,
                template_used=template_obj,
                status='SENT',
                sent_at=timezone.now(),
                provider='django-mail'
            )

            return {'success': True, 'message': 'Email envoyé'}

        except Exception as e:
            EmailLog.objects.create(
                recipient_email=to_email,
                subject=subject,
                body_html=html_content,
                body_text=text_content,
                status='FAILED',
                error_message=str(e)
            )

            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_template_email(to_email, template_name, context):
        """Envoie un email depuis un template"""
        try:
            template = EmailTemplate.objects.get(name=template_name, is_active=True)
        except EmailTemplate.DoesNotExist:
            return {'success': False, 'error': 'Template not found'}

        # Remplacer les variables
        subject = template.subject
        html_content = template.html_content
        text_content = template.text_content

        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"  # {{key}}
            subject = subject.replace(placeholder, str(value))
            html_content = html_content.replace(placeholder, str(value))
            text_content = text_content.replace(placeholder, str(value))

        return EmailService.send_email(to_email, subject, html_content, text_content, template_name)


class SMSService:
    """Service d'envoi de SMS"""

    @staticmethod
    def send_sms(to_phone, message, template_name=None):
        """
        Envoie un SMS

        En production, utiliser Twilio ou Africa's Talking:

        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        """
        try:
            # Simulation
            template_obj = None
            if template_name:
                template_obj = SMSTemplate.objects.filter(name=template_name).first()

            SMSLog.objects.create(
                recipient_phone=to_phone,
                content=message[:160],
                template_used=template_obj,
                status='SENT',  # Simulation
                sent_at=timezone.now(),
                delivered_at=timezone.now(),
                provider='simulation',
                cost=0.05  # Simulation
            )

            return {'success': True, 'message': 'SMS envoyé'}

        except Exception as e:
            SMSLog.objects.create(
                recipient_phone=to_phone,
                content=message[:160],
                status='FAILED',
                error_message=str(e)
            )

            return {'success': False, 'error': str(e)}

    @staticmethod
    def send_template_sms(to_phone, template_name, context):
        """Envoie un SMS depuis un template"""
        try:
            template = SMSTemplate.objects.get(name=template_name, is_active=True)
        except SMSTemplate.DoesNotExist:
            return {'success': False, 'error': 'Template not found'}

        # Remplacer les variables
        content = template.content

        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))

        return SMSService.send_sms(to_phone, content, template_name)


class NotificationService:
    """Service multi-canal de notifications"""

    @staticmethod
    def send_notification(user, notification_type, template_name, context, priority=5):
        """Envoie une notification (email, SMS, ou les deux)"""
        from .models import NotificationQueue

        results = {}

        if 'email' in notification_type:
            NotificationQueue.objects.create(
                notification_type='EMAIL',
                recipient_id=user.id,
                recipient_email=user.email,
                template_name=template_name,
                context_data=context,
                priority=priority
            )
            results['email'] = 'queued'

        if 'sms' in notification_type and user.phone:
            NotificationQueue.objects.create(
                notification_type='SMS',
                recipient_id=user.id,
                recipient_phone=user.phone,
                template_name=template_name,
                context_data=context,
                priority=priority
            )
            results['sms'] = 'queued'

        return results

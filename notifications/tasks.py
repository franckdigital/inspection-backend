from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def retry_failed_emails():
    """
    Retente l'envoi des emails échoués ou bounced depuis moins de 24h.
    Planifié toutes les 30 minutes via CELERYBEAT_SCHEDULE.
    """
    from .models import EmailLog
    from .services import EmailService

    threshold = timezone.now() - timedelta(hours=24)

    failed = EmailLog.objects.filter(
        status__in=['FAILED', 'BOUNCED'],
        created_at__gte=threshold,
        retry_count__lt=3,
    )

    retried = 0
    for log in failed:
        try:
            result = EmailService.send_email(
                to_email=log.to_email,
                subject=log.subject,
                html_content=log.html_content,
                text_content=log.text_content or '',
            )
            if result.get('success'):
                log.status = 'SENT'
                log.sent_at = timezone.now()
            else:
                log.status = 'FAILED'
            log.retry_count = (log.retry_count or 0) + 1
            log.save(update_fields=['status', 'sent_at', 'retry_count'])
            retried += 1
        except Exception:
            log.retry_count = (log.retry_count or 0) + 1
            log.save(update_fields=['retry_count'])

    return {'retried': retried}


@shared_task
def retry_failed_sms():
    """Retente l'envoi des SMS échoués depuis moins de 24h."""
    from .models import SMSLog
    from .services import SMSService

    threshold = timezone.now() - timedelta(hours=24)

    failed = SMSLog.objects.filter(
        status='FAILED',
        created_at__gte=threshold,
        retry_count__lt=3,
    )

    retried = 0
    for log in failed:
        try:
            result = SMSService.send_sms(
                to_phone=log.to_phone,
                message=log.message,
            )
            if result.get('success'):
                log.status = 'SENT'
                log.sent_at = timezone.now()
            log.retry_count = (log.retry_count or 0) + 1
            log.save(update_fields=['status', 'sent_at', 'retry_count'])
            retried += 1
        except Exception:
            log.retry_count = (log.retry_count or 0) + 1
            log.save(update_fields=['retry_count'])

    return {'retried': retried}


@shared_task
def process_pending_notifications():
    """Traite la file des notifications en attente (statut PENDING)."""
    from .models import EmailLog
    from .services import EmailService

    pending = EmailLog.objects.filter(status='PENDING').order_by('created_at')[:100]

    sent = 0
    for log in pending:
        try:
            result = EmailService.send_email(
                to_email=log.to_email,
                subject=log.subject,
                html_content=log.html_content,
                text_content=log.text_content or '',
            )
            log.status = 'SENT' if result.get('success') else 'FAILED'
            log.sent_at = timezone.now() if log.status == 'SENT' else None
            log.save(update_fields=['status', 'sent_at'])
            if log.status == 'SENT':
                sent += 1
        except Exception as exc:
            log.status = 'FAILED'
            log.error_message = str(exc)
            log.save(update_fields=['status', 'error_message'])

    return {'processed': len(pending), 'sent': sent}

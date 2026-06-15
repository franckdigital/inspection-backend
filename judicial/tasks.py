from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def send_hearing_reminders():
    """
    Envoie des rappels 48h et 24h avant chaque audience programmée.
    Planifié toutes les heures via CELERYBEAT_SCHEDULE.
    """
    from .models import Hearing
    from complaints.models import ComplaintNotification

    now = timezone.now()
    reminders_sent = 0

    for hours_before, label in [(48, '48h'), (24, '24h')]:
        window_start = now + timedelta(hours=hours_before - 1)
        window_end   = now + timedelta(hours=hours_before)

        upcoming = Hearing.objects.filter(
            status='SCHEDULED',
            scheduled_date__gte=window_start,
            scheduled_date__lt=window_end,
        ).select_related('procedure__complaint', 'procedure__plaintiff')

        for hearing in upcoming:
            procedure = hearing.procedure
            complaint = procedure.complaint

            # Notifier le plaignant
            if procedure.plaintiff:
                ComplaintNotification.objects.create(
                    complaint=complaint,
                    recipient=procedure.plaintiff,
                    message=(
                        f'Rappel ({label}) : audience prévue le '
                        f'{hearing.scheduled_date.strftime("%d/%m/%Y à %H:%M")} '
                        f'— {hearing.location or "lieu à confirmer"}'
                    )
                )

            # Notifier le chargé de dossier
            if procedure.case_officer:
                ComplaintNotification.objects.create(
                    complaint=complaint,
                    recipient=procedure.case_officer,
                    message=(
                        f'Rappel ({label}) : audience {procedure.reference_number} '
                        f'le {hearing.scheduled_date.strftime("%d/%m/%Y à %H:%M")}'
                    )
                )

            reminders_sent += 1

    return {'reminders_sent': reminders_sent}


@shared_task
def alert_overdue_procedures():
    """Alerte les chargés de dossier pour les procédures sans activité depuis 30 jours."""
    from .models import JudicialProcedure
    from complaints.models import ComplaintNotification

    threshold = timezone.now() - timedelta(days=30)

    overdue = JudicialProcedure.objects.filter(
        status__in=['PREPARATION', 'SUBMITTED', 'HEARING_SCHEDULED'],
        updated_at__lte=threshold,
        case_officer__isnull=False,
    )

    alerted = 0
    for procedure in overdue:
        ComplaintNotification.objects.create(
            complaint=procedure.complaint,
            recipient=procedure.case_officer,
            message=(
                f'[ALERTE] Procédure {procedure.reference_number} sans activité '
                f'depuis plus de 30 jours — veuillez mettre à jour le dossier.'
            )
        )
        alerted += 1

    return {'alerted': alerted}

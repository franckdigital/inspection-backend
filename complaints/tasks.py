from celery import shared_task
from django.utils import timezone
from datetime import timedelta


# Délais d'escalade par priorité (en heures)
ESCALATION_DELAYS = {
    'URGENT': 48,
    'HIGH': 168,       # 7 jours
    'MEDIUM': 360,     # 15 jours
    'LOW': 720,        # 30 jours
}


@shared_task
def escalate_overdue_complaints():
    """
    Escalade automatiquement les plaintes dont le délai de traitement est dépassé.
    Planifié toutes les heures via CELERYBEAT_SCHEDULE.
    """
    from .models import Complaint, ComplaintStatusHistory, ComplaintNotification
    from users.models import User

    now = timezone.now()
    escalated_count = 0

    for priority, delay_hours in ESCALATION_DELAYS.items():
        deadline = now - timedelta(hours=delay_hours)

        overdue = Complaint.objects.filter(
            priority=priority,
            status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS'],
            created_at__lte=deadline,
            is_escalated=False
        )

        for complaint in overdue:
            # Rechercher un chef d'inspection disponible
            chef = User.objects.filter(
                user_type='CHEF_INSPECTION',
                is_active=True
            ).first()

            old_status = complaint.status
            complaint.status = 'ESCALATED'
            complaint.is_escalated = True
            complaint.save(update_fields=['status', 'is_escalated'])

            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                from_status=old_status,
                to_status='ESCALATED',
                reason=f'Escalade automatique — délai {priority} ({delay_hours}h) dépassé',
            )

            if chef:
                ComplaintNotification.objects.create(
                    complaint=complaint,
                    recipient=chef,
                    message=(
                        f'[ALERTE] Plainte #{complaint.complaint_number} en retard '
                        f'(priorité {priority}, {delay_hours}h dépassées) — escalade automatique'
                    )
                )

            escalated_count += 1

    return {'escalated': escalated_count, 'timestamp': now.isoformat()}


@shared_task
def send_complaint_reminders():
    """Envoie des rappels aux inspecteurs pour les plaintes assignées sans activité depuis 72h."""
    from .models import Complaint, ComplaintNotification

    threshold = timezone.now() - timedelta(hours=72)

    stale = Complaint.objects.filter(
        status='ASSIGNED',
        assigned_to__isnull=False,
        updated_at__lte=threshold
    )

    for complaint in stale:
        ComplaintNotification.objects.create(
            complaint=complaint,
            recipient=complaint.assigned_to,
            message=(
                f'Rappel : la plainte #{complaint.complaint_number} (priorité {complaint.priority}) '
                f'n\'a pas été mise à jour depuis plus de 72h.'
            )
        )

    return {'reminders_sent': stale.count()}

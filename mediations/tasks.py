"""
Tâches Celery pour la gestion automatique des convocations et des délais.

Planification recommandée dans celery beat (config/celery.py) :
    'check-convocation-deadlines': {
        'task': 'mediations.tasks.check_convocation_deadlines',
        'schedule': crontab(hour=7, minute=0),   # Chaque jour à 7h00
    },
    'check-session-reminders': {
        'task': 'mediations.tasks.send_session_reminders',
        'schedule': crontab(hour=6, minute=30),  # Chaque jour à 6h30
    },
    'check-agreement-deadlines': {
        'task': 'mediations.tasks.check_agreement_execution_deadlines',
        'schedule': crontab(hour=8, minute=0),   # Chaque jour à 8h00
    },
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

# Délai sans réponse avant première relance automatique (heures)
FIRST_RELANCE_AFTER_HOURS = 48
# Délai entre chaque relance (heures)
RELANCE_INTERVAL_HOURS = 24
# Nombre max de relances automatiques avant escalade hiérarchique
MAX_AUTO_RELANCES = 3
# Délai avant la séance pour envoyer un rappel aux participants confirmés (heures)
REMINDER_BEFORE_SESSION_HOURS = 24


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def check_convocation_deadlines(self):
    """
    Vérifie quotidiennement les convocations sans accusé de réception.
    Pour chaque participant non-répondant :
      - Si < MAX_AUTO_RELANCES : relance via le prochain canal disponible
      - Si >= MAX_AUTO_RELANCES : escalade hiérarchique
    """
    from .models import MediationParticipant, Mediation
    from .notifications import (
        send_convocation_email, send_convocation_sms,
        send_convocation_inapp, notify_hierarchy_no_response,
    )

    now = timezone.now()
    first_relance_threshold = now - timedelta(hours=FIRST_RELANCE_AFTER_HOURS)
    relance_interval_threshold = now - timedelta(hours=RELANCE_INTERVAL_HOURS)

    # Participants convoqués mais sans accusé de réception, séance pas encore passée
    pending = MediationParticipant.objects.filter(
        convocation_sent=True,
        acknowledged_at__isnull=True,
        manually_acknowledged=False,
        mediation__status='SCHEDULED',
        mediation__session_date__gt=now,
    ).select_related('participant', 'mediation__complaint__enterprise')

    escalated_count = 0
    relanced_count  = 0

    for participant in pending:
        mediation = participant.mediation

        # Première relance : delai depuis première convocation écoulé
        if participant.convocation_attempts == 1:
            if participant.convoked_at and participant.convoked_at <= first_relance_threshold:
                _do_relance(participant, mediation)
                relanced_count += 1

        # Relances suivantes : délai entre deux relances écoulé
        elif participant.convocation_attempts > 1:
            if participant.last_attempt_at and participant.last_attempt_at <= relance_interval_threshold:
                if participant.convocation_attempts < MAX_AUTO_RELANCES:
                    _do_relance(participant, mediation)
                    relanced_count += 1
                else:
                    # Seuil atteint → escalade
                    notify_hierarchy_no_response(mediation)
                    escalated_count += 1
                    logger.warning(
                        "Escalade auto — médiation %s, participant %s (%d tentatives)",
                        mediation.id, participant.display_name, participant.convocation_attempts
                    )

    logger.info(
        "check_convocation_deadlines: %d relances, %d escalades",
        relanced_count, escalated_count
    )
    return {'relanced': relanced_count, 'escalated': escalated_count}


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_session_reminders(self):
    """
    Envoie un rappel 24h avant la séance à tous les participants
    ayant accusé réception (ou confirmés manuellement).
    """
    from .models import Mediation, MediationParticipant
    from .notifications import send_convocation_email, send_convocation_sms

    now = timezone.now()
    window_start = now + timedelta(hours=REMINDER_BEFORE_SESSION_HOURS - 1)
    window_end   = now + timedelta(hours=REMINDER_BEFORE_SESSION_HOURS + 1)

    upcoming = Mediation.objects.filter(
        status='SCHEDULED',
        session_date__range=(window_start, window_end),
    ).prefetch_related('participants')

    sent_count = 0
    for mediation in upcoming:
        for participant in mediation.participants.all():
            if participant.is_acknowledged:
                send_convocation_email(participant, mediation)
                send_convocation_sms(participant, mediation)
                sent_count += 1

    logger.info("send_session_reminders: %d rappels envoyés", sent_count)
    return {'reminders_sent': sent_count}


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def check_agreement_execution_deadlines(self):
    """
    Vérifie les accords dont la date limite d'exécution est dépassée
    et dont le statut est toujours SIGNED (pas encore EXECUTED).
    Notifie le médiateur et le plaignant.
    """
    from .models import Agreement
    from complaints.models import ComplaintNotification

    overdue = Agreement.objects.filter(
        status='SIGNED',
        execution_deadline__lt=timezone.now().date(),
    ).select_related('mediation__mediator', 'mediation__complaint__complainant')

    notified_count = 0
    for agreement in overdue:
        mediation = agreement.mediation
        complaint = mediation.complaint
        deadline  = agreement.execution_deadline.strftime('%d/%m/%Y')

        if mediation.mediator:
            ComplaintNotification.objects.get_or_create(
                complaint=complaint,
                recipient=mediation.mediator,
                message=(
                    f"⚠️ L'accord sur la plainte {complaint.complaint_number} "
                    f"n'a pas été exécuté à la date prévue ({deadline}). "
                    f"Veuillez vérifier l'état d'exécution."
                ),
            )

        ComplaintNotification.objects.get_or_create(
            complaint=complaint,
            recipient=complaint.complainant,
            message=(
                f"L'employeur n'a pas respecté l'accord signé à la date prévue ({deadline}). "
                f"Vous pouvez signaler cette violation à l'inspection du travail."
            ),
        )
        notified_count += 1

    logger.info("check_agreement_execution_deadlines: %d accords en retard notifiés", notified_count)
    return {'overdue_agreements_notified': notified_count}


@shared_task
def auto_escalate_long_pending_mediations():
    """
    Escalade les médiations planifiées depuis plus de 30 jours sans avancement.
    """
    from .models import Mediation
    from complaints.models import ComplaintStatusHistory

    threshold = timezone.now() - timedelta(days=30)
    stalled = Mediation.objects.filter(
        status='SCHEDULED',
        created_at__lte=threshold,
    ).select_related('complaint', 'no_show_reported_by')

    count = 0
    for mediation in stalled:
        complaint = mediation.complaint
        if complaint.status == 'MEDIATION':
            complaint.status = 'ESCALATED'
            complaint.save()
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                from_status='MEDIATION',
                to_status='ESCALATED',
                changed_by=None,
                reason='Escalade automatique — médiation sans avancement depuis 30 jours',
            )
            count += 1

    logger.info("auto_escalate_long_pending_mediations: %d dossiers escaladés", count)
    return {'escalated': count}


# ── Helper interne ────────────────────────────────────────────────────────────

def _do_relance(participant, mediation):
    """Détermine le canal de relance et envoie."""
    from .notifications import send_convocation_email, send_convocation_sms, send_convocation_inapp

    participant.last_attempt_at = timezone.now()
    participant.convocation_attempts += 1
    participant.save()

    # Rotation des canaux : 1→EMAIL, 2→SMS, 3→PUSH
    attempt = participant.convocation_attempts
    if attempt % 3 == 1:
        send_convocation_email(participant, mediation)
    elif attempt % 3 == 2:
        send_convocation_sms(participant, mediation)
    else:
        send_convocation_inapp(participant, mediation)

    logger.info(
        "Relance auto — médiation %s, participant %s, tentative %d",
        mediation.id, participant.display_name, participant.convocation_attempts
    )

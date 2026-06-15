"""
Envoi réel des convocations — email, SMS, notification in-app.
Toutes les fonctions sont sans-exception : elles loguent les erreurs
sans faire planter le flux principal.
"""

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ── Helpers ──────────────────────────────────────────────────────────────────

def _build_convocation_url(token: str) -> str:
    base = getattr(settings, 'FRONTEND_URL', 'https://e-inspection.ci')
    return f"{base}/convocation/confirmer/{token}/"


def _build_convocation_email_body(participant, mediation, confirm_url: str) -> str:
    name = participant.display_name
    date = mediation.session_date.strftime('%d/%m/%Y à %H:%M')
    complaint_no = mediation.complaint.complaint_number

    if mediation.session_type == 'PRESENTIAL':
        lieu_ligne = f"Lieu      : {mediation.location}"
    elif mediation.session_type == 'ONLINE':
        lieu_ligne = f"Lien visio : {mediation.meeting_link}"
    else:
        lieu_ligne = f"Lieu      : {mediation.location}\nLien visio : {mediation.meeting_link}"

    return f"""Madame, Monsieur {name},

Dans le cadre du traitement de la plainte n° {complaint_no}, vous êtes convoqué(e)
à une séance de médiation organisée par l'Inspection du Travail de Côte d'Ivoire.

──────────────────────────────────────────
Date      : {date}
{lieu_ligne}
Type      : {mediation.get_session_type_display()}
──────────────────────────────────────────

Votre présence est obligatoire. En cas d'impossibilité, veuillez contacter
l'Inspection du Travail au plus tôt.

⚠️  Tout défaut de comparution non justifié constitue une infraction passible
de sanctions conformément au Code du Travail ivoirien (Loi n° 2015-532).

Merci de confirmer la réception de cette convocation en cliquant sur le lien
ci-dessous :

  {confirm_url}

Cordialement,
Direction Générale du Travail — Côte d'Ivoire
Plateforme e-Inspection du Travail
"""


def _build_sms_body(participant, mediation, confirm_url: str) -> str:
    date = mediation.session_date.strftime('%d/%m/%Y %H:%M')
    no = mediation.complaint.complaint_number
    return (
        f"DGT-CI | Plainte {no} : vous êtes convoqué(e) à une séance de médiation "
        f"le {date}. Confirmez : {confirm_url} "
        f"Tout défaut expose à des sanctions (Code Travail CI)."
    )


# ── Envoi email ───────────────────────────────────────────────────────────────

def send_convocation_email(participant, mediation) -> bool:
    """Envoie la convocation par e-mail. Retourne True si succès."""
    email = participant.email or (participant.participant.email if participant.participant else None)
    if not email:
        logger.warning("send_convocation_email: pas d'email pour participant %s", participant.id)
        return False

    confirm_url = _build_convocation_url(str(participant.acknowledgment_token))
    body = _build_convocation_email_body(participant, mediation, confirm_url)

    try:
        send_mail(
            subject=f"[DGT-CI] Convocation médiation — Plainte {mediation.complaint.complaint_number}",
            message=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@travail.ci'),
            recipient_list=[email],
            fail_silently=False,
        )
        _log_attempt(participant, 'EMAIL', 'DELIVERED')
        return True
    except Exception as exc:
        logger.error("send_convocation_email error: %s", exc)
        _log_attempt(participant, 'EMAIL', 'FAILED', str(exc))
        return False


# ── Envoi SMS ─────────────────────────────────────────────────────────────────

def send_convocation_sms(participant, mediation) -> bool:
    """Envoie la convocation par SMS via le gateway configuré. Retourne True si succès."""
    phone = participant.phone or (
        str(participant.participant.phone_number)
        if participant.participant and participant.participant.phone_number
        else None
    )
    if not phone:
        logger.warning("send_convocation_sms: pas de téléphone pour participant %s", participant.id)
        return False

    confirm_url = _build_convocation_url(str(participant.acknowledgment_token))
    body = _build_sms_body(participant, mediation, confirm_url)

    # Intégration gateway SMS ivoirien (Orange CI / CinetPay SMS / Bizao)
    # Configurer SMS_GATEWAY_URL et SMS_GATEWAY_KEY dans settings.py
    gateway_url = getattr(settings, 'SMS_GATEWAY_URL', None)
    gateway_key = getattr(settings, 'SMS_GATEWAY_KEY', None)

    if not gateway_url:
        logger.warning("send_convocation_sms: SMS_GATEWAY_URL non configuré — SMS simulé")
        logger.info("SMS simulé → %s : %s", phone, body)
        _log_attempt(participant, 'SMS', 'SENT')
        return True

    try:
        import requests
        resp = requests.post(
            gateway_url,
            json={'to': phone, 'message': body, 'api_key': gateway_key},
            timeout=10,
        )
        resp.raise_for_status()
        provider_id = resp.json().get('message_id', '')
        _log_attempt(participant, 'SMS', 'DELIVERED', provider_message_id=provider_id)
        return True
    except Exception as exc:
        logger.error("send_convocation_sms error: %s", exc)
        _log_attempt(participant, 'SMS', 'FAILED', str(exc))
        return False


# ── Notifications in-app ──────────────────────────────────────────────────────

def send_convocation_inapp(participant, mediation) -> bool:
    """Crée une notification in-app pour les participants ayant un compte."""
    user = participant.participant
    if not user:
        return False

    try:
        from complaints.models import ComplaintNotification
        date = mediation.session_date.strftime('%d/%m/%Y à %H:%M')
        ComplaintNotification.objects.create(
            complaint=mediation.complaint,
            recipient=user,
            message=(
                f"Vous êtes convoqué(e) à une séance de médiation "
                f"le {date} — Plainte {mediation.complaint.complaint_number}"
            )
        )
        _log_attempt(participant, 'PUSH', 'DELIVERED')
        return True
    except Exception as exc:
        logger.error("send_convocation_inapp error: %s", exc)
        return False


# ── Escalade hiérarchique ─────────────────────────────────────────────────────

def notify_hierarchy_no_response(mediation) -> None:
    """Notifie le chef d'inspection et le directeur régional si l'employeur ne répond pas."""
    try:
        from complaints.models import ComplaintNotification
        complaint = mediation.complaint

        recipients = []
        # Chef d'inspection de la zone
        if complaint.inspection_zone and complaint.inspection_zone.head:
            recipients.append(complaint.inspection_zone.head)
        # Directeur régional si disponible
        if complaint.assigned_to and hasattr(complaint.assigned_to, 'superior') \
                and complaint.assigned_to.superior:
            recipients.append(complaint.assigned_to.superior)

        for recipient in recipients:
            ComplaintNotification.objects.create(
                complaint=complaint,
                recipient=recipient,
                message=(
                    f"⚠️ ALERTE — L'employeur de la plainte {complaint.complaint_number} "
                    f"ne répond pas aux convocations de médiation ({mediation.convocation_attempts_count} tentatives). "
                    f"Veuillez intervenir."
                )
            )
    except Exception as exc:
        logger.error("notify_hierarchy_no_response error: %s", exc)


# ── Logger interne ────────────────────────────────────────────────────────────

def _log_attempt(participant, channel: str, status: str,
                 error_detail: str = '', provider_message_id: str = '') -> None:
    try:
        from .models import ConvocationAttempt
        ConvocationAttempt.objects.create(
            participant=participant,
            channel=channel,
            status=status,
            error_detail=error_detail,
            provider_message_id=provider_message_id,
        )
    except Exception as exc:
        logger.error("_log_attempt error: %s", exc)

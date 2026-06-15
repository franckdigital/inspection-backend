"""
complaints/services.py
Logique d'assignation automatique des plaintes aux inspecteurs.

Flux :
  plainte créée
     └─> find_zone_for_commune()   : commune -> InspectionZone
     └─> find_best_inspector()     : zone -> inspecteur le moins chargé
     └─> assign_complaint()        : enregistre l'assignation + notifications
     └─> si aucun inspecteur dispo : notifie tous les CHEF_INSPECTION
"""
import logging

from django.db.models import Count, Q

logger = logging.getLogger(__name__)

# Statuts considérés comme "actifs" pour le calcul de charge
ACTIVE_STATUSES = (
    'PENDING', 'ASSIGNED', 'IN_PROGRESS',
    'UNDER_INVESTIGATION', 'MEDIATION', 'ESCALATED',
)

# Seuil de surcharge : au-delà, l'inspecteur est considéré "chargé"
OVERLOAD_THRESHOLD = 15


# ─── Résolution zone ─────────────────────────────────────────────────────────

def find_zone_for_commune(commune_name: str):
    """
    Retourne l'InspectionZone correspondant à la commune (insensible à la casse,
    correspondance partielle). Retourne None si aucune commune active trouvée.
    """
    from inspections.models import Commune
    if not commune_name or not commune_name.strip():
        return None
    commune = (
        Commune.objects
        .filter(name__icontains=commune_name.strip(), is_active=True)
        .select_related('zone')
        .first()
    )
    if commune and commune.zone and commune.zone.is_active:
        return commune.zone
    return None


# ─── Sélection de l'inspecteur ───────────────────────────────────────────────

def find_best_inspector(zone):
    """
    Retourne l'inspecteur actif dans la zone avec le moins de plaintes actives.
    Retourne None si la zone n'a aucun inspecteur disponible.
    """
    from inspections.models import InspectorZoneAssignment
    from users.models import User

    inspector_ids = list(
        InspectorZoneAssignment.objects
        .filter(zone=zone, is_active=True)
        .values_list('inspector_id', flat=True)
    )
    if not inspector_ids:
        return None

    inspector = (
        User.objects
        .filter(id__in=inspector_ids, user_type='INSPECTEUR', is_active=True)
        .annotate(
            active_count=Count(
                'assigned_complaints',
                filter=Q(assigned_complaints__status__in=ACTIVE_STATUSES),
            )
        )
        .order_by('active_count')
        .first()
    )
    return inspector


def get_zone_inspectors_load(zone):
    """
    Retourne la liste de tous les inspecteurs de la zone avec leur charge courante.
    Utilisé par l'endpoint suggest_delegates pour afficher les collègues disponibles.
    """
    from inspections.models import InspectorZoneAssignment
    from users.models import User

    inspector_ids = list(
        InspectorZoneAssignment.objects
        .filter(zone=zone, is_active=True)
        .values_list('inspector_id', flat=True)
    )
    return (
        User.objects
        .filter(id__in=inspector_ids, user_type='INSPECTEUR', is_active=True)
        .annotate(
            active_count=Count(
                'assigned_complaints',
                filter=Q(assigned_complaints__status__in=ACTIVE_STATUSES),
            )
        )
        .order_by('active_count')
        .values('id', 'first_name', 'last_name', 'email', 'active_count')
    )


# ─── Exécution de l'assignation ──────────────────────────────────────────────

def _log_history(complaint, from_status, to_status, changed_by, reason):
    from .models import ComplaintStatusHistory
    ComplaintStatusHistory.objects.create(
        complaint=complaint,
        from_status=from_status,
        to_status=to_status,
        changed_by=changed_by,
        reason=reason,
    )


def _notify(complaint, recipient, message):
    from .models import ComplaintNotification
    ComplaintNotification.objects.create(
        complaint=complaint,
        recipient=recipient,
        message=message,
    )


def assign_complaint(complaint, inspector, assigned_by=None, reason=''):
    """
    Effectue l'assignation :
      - Met à jour complaint.assigned_to et complaint.status
      - Enregistre dans l'historique de statut
      - Notifie l'inspecteur et le plaignant
    """
    old_status = complaint.status
    complaint.assigned_to = inspector
    complaint.status = 'ASSIGNED'
    complaint.save(update_fields=['assigned_to', 'status', 'updated_at'])

    commune_label = complaint.workplace_commune or complaint.workplace_address[:60]
    zone_label = complaint.inspection_zone.name if complaint.inspection_zone else 'inconnue'

    _log_history(
        complaint,
        from_status=old_status,
        to_status='ASSIGNED',
        changed_by=assigned_by,
        reason=reason or f'Assignation automatique à {inspector.get_full_name()} — zone {zone_label}',
    )

    _notify(
        complaint, inspector,
        (
            f'Nouvelle plainte #{complaint.complaint_number} assignée : '
            f'{complaint.get_complaint_type_display()} — '
            f'commune : {commune_label} — '
            f'priorité : {complaint.get_priority_display()}'
        ),
    )

    _notify(
        complaint, complaint.complainant,
        (
            f'Votre plainte #{complaint.complaint_number} a été prise en charge par '
            f'{inspector.get_full_name()}, Inspecteur(trice) du Travail. '
            f'Vous serez contacté(e) prochainement.'
        ),
    )

    logger.info(
        'Complaint %s assigned to inspector %s (id=%s) in zone %s',
        complaint.complaint_number, inspector.get_full_name(), inspector.pk, zone_label,
    )


# ─── Point d'entrée principal ─────────────────────────────────────────────────

def auto_assign_complaint(complaint):
    """
    Appelé immédiatement après la création d'une plainte.

    1. Résout la commune -> zone -> enregistre inspection_zone
    2. Choisit l'inspecteur le moins chargé dans cette zone
    3. Assigne ; si aucun inspecteur disponible, laisse PENDING
       et avertit tous les CHEF_INSPECTION
    """
    # 1) Résolution de la zone
    zone = find_zone_for_commune(complaint.workplace_commune)
    if zone:
        complaint.inspection_zone = zone
        complaint.save(update_fields=['inspection_zone', 'updated_at'])
        logger.info(
            'Complaint %s: commune "%s" → zone "%s"',
            complaint.complaint_number, complaint.workplace_commune, zone.name,
        )
    else:
        logger.warning(
            'Complaint %s: aucune zone trouvée pour la commune "%s"',
            complaint.complaint_number, complaint.workplace_commune,
        )

    # 2) Sélection de l'inspecteur
    inspector = find_best_inspector(zone) if zone else None

    # 3) Assignation ou alerte manuelle
    if inspector:
        assign_complaint(
            complaint,
            inspector,
            assigned_by=None,
            reason=(
                f'Assignation automatique — commune "{complaint.workplace_commune}" → '
                f'zone "{zone.name}" — charge : {inspector.active_count} plainte(s) active(s)'
            ),
        )
    else:
        _notify_pending_to_chefs(complaint)


def _notify_pending_to_chefs(complaint):
    """Notifie tous les CHEF_INSPECTION qu'une plainte attend une assignation manuelle."""
    from users.models import User
    chefs = User.objects.filter(user_type='CHEF_INSPECTION', is_active=True)
    commune_label = complaint.workplace_commune or 'commune non renseignée'
    for chef in chefs:
        _notify(
            complaint, chef,
            (
                f'⚠ Plainte #{complaint.complaint_number} sans inspecteur disponible '
                f'(commune : {commune_label}). Assignation manuelle requise.'
            ),
        )
    logger.warning(
        'Complaint %s left PENDING — %d chef(s) notified.',
        complaint.complaint_number, chefs.count(),
    )

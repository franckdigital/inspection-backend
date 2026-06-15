from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


@shared_task
def generate_monthly_payslips():
    """
    Génère automatiquement les bulletins de paie du mois en cours
    pour tous les contrats actifs.
    Planifié le 1er de chaque mois à 06h00 via CELERYBEAT_SCHEDULE.
    """
    from .models import DomesticContract, MonthlyPayslip

    today = timezone.now().date()
    month = today.month
    year = today.year

    contracts = DomesticContract.objects.filter(
        status='ACTIVE',
        start_date__lte=today,
    ).select_related('worker', 'employer')

    created_count = 0

    for contract in contracts:
        _, created = MonthlyPayslip.objects.get_or_create(
            contract=contract,
            month=month,
            year=year,
            defaults={
                'base_salary': contract.base_salary,
                'net_salary': _compute_net(contract),
                'status': 'PENDING',
            }
        )
        if created:
            created_count += 1

    return {'month': f'{year}-{month:02d}', 'payslips_created': created_count}


def _compute_net(contract) -> Decimal:
    """Calcule le salaire net approximatif (avant déduction fiscale détaillée)."""
    gross = contract.base_salary or Decimal('0')
    # CNPS employé CI : ~6.3 % du brut
    cnps = gross * Decimal('0.063')
    return (gross - cnps).quantize(Decimal('0.01'))


@shared_task
def send_leave_approval_reminders():
    """
    Relance les employeurs qui n'ont pas encore répondu aux demandes de congé
    depuis plus de 48h.
    """
    from .models import LeaveRequest
    from complaints.models import ComplaintNotification

    threshold = timezone.now() - timedelta(hours=48)

    pending = LeaveRequest.objects.filter(
        status='PENDING',
        created_at__lte=threshold,
    ).select_related('contract__employer__user', 'worker__user')

    reminders = 0
    for leave in pending:
        employer_user = getattr(getattr(leave.contract, 'employer', None), 'user', None)
        if employer_user:
            # Utiliser le système de notification interne
            from notifications.services import EmailService
            EmailService.send_email(
                to_email=employer_user.email,
                subject='Demande de congé en attente de réponse',
                html_content=(
                    f'<p>La demande de congé de '
                    f'{leave.worker.user.get_full_name()} '
                    f'({leave.start_date} → {leave.end_date}) '
                    f'attend votre réponse depuis plus de 48h.</p>'
                ),
            )
            reminders += 1

    return {'reminders_sent': reminders}


@shared_task
def expire_old_contracts():
    """Marque comme EXPIRED les contrats dont la date de fin est dépassée."""
    from .models import DomesticContract

    today = timezone.now().date()
    expired = DomesticContract.objects.filter(
        status='ACTIVE',
        end_date__lt=today,
        end_date__isnull=False,
    )
    count = expired.update(status='EXPIRED')
    return {'expired_contracts': count}

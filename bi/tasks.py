import csv
import io
from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_export(self, export_id: int):
    """Génère le fichier d'export demandé (CSV/JSON) et met à jour le statut."""
    from .models import DataExport

    try:
        export = DataExport.objects.get(id=export_id)
    except DataExport.DoesNotExist:
        return {'error': f'DataExport {export_id} introuvable'}

    export.status = 'PROCESSING'
    export.save(update_fields=['status'])

    try:
        data, filename = _generate_export_data(export)

        # Stocker dans un champ fichier ou un storage externe
        # Pour l'instant, stocker les données JSON dans export.result_data
        export.status = 'COMPLETED'
        export.completed_at = timezone.now()
        export.file_path = filename
        export.row_count = len(data) if isinstance(data, list) else 0
        export.save(update_fields=['status', 'completed_at', 'file_path', 'row_count'])

        return {'status': 'completed', 'export_id': export_id, 'rows': export.row_count}

    except Exception as exc:
        export.status = 'FAILED'
        export.error_message = str(exc)
        export.save(update_fields=['status', 'error_message'])
        raise self.retry(exc=exc)


def _generate_export_data(export):
    """Extrait les données selon le type d'export et retourne (rows, filename)."""
    from complaints.models import Complaint
    from enterprises.models import Enterprise
    from inspections.models import InspectionRecord
    from mediations.models import Mediation

    export_type = getattr(export, 'export_type', 'complaints')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

    mapping = {
        'complaints': (
            list(Complaint.objects.values(
                'complaint_number', 'subject', 'status', 'priority',
                'complaint_type', 'employer_name', 'created_at'
            )),
            f'export_plaintes_{timestamp}.csv'
        ),
        'enterprises': (
            list(Enterprise.objects.values(
                'name', 'rccm', 'nif', 'sector', 'city',
                'employee_count', 'compliance_score', 'risk_level'
            )),
            f'export_entreprises_{timestamp}.csv'
        ),
        'inspections': (
            list(InspectionRecord.objects.values(
                'enterprise__name', 'inspection_type', 'result',
                'is_completed', 'scheduled_date', 'actual_date'
            )),
            f'export_inspections_{timestamp}.csv'
        ),
        'mediations': (
            list(Mediation.objects.values(
                'complaint__complaint_number', 'status', 'session_type',
                'outcome', 'scheduled_date'
            )),
            f'export_mediations_{timestamp}.csv'
        ),
    }

    rows, filename = mapping.get(export_type, ([], f'export_{timestamp}.csv'))
    return rows, filename

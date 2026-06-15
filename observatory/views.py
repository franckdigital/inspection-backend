from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models.functions import TruncDate, TruncMonth

from complaints.models import Complaint
from enterprises.models import Enterprise
from inspections.models import InspectionRecord
from mediations.models import Mediation
from core.permissions import IsInspecteur, IsDirecteurGeneral


class NationalStatsView(APIView):
    """Statistiques nationales temps réel"""
    permission_classes = [IsInspecteur]

    def get(self, request):
        # Plaintes
        total_complaints = Complaint.objects.count()
        pending_complaints = Complaint.objects.filter(status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']).count()
        resolved_complaints = Complaint.objects.filter(status='RESOLVED').count()

        # Entreprises
        total_enterprises = Enterprise.objects.count()
        at_risk_enterprises = Enterprise.objects.filter(risk_level__in=['HIGH', 'CRITICAL']).count()
        avg_compliance = Enterprise.objects.aggregate(avg=Avg('compliance_score'))['avg'] or 0

        # Inspections
        total_inspections = InspectionRecord.objects.count()
        completed_inspections = InspectionRecord.objects.filter(is_completed=True).count()

        # Médiations
        total_mediations = Mediation.objects.count()
        successful_mediations = Mediation.objects.filter(outcome='AGREEMENT').count()

        return Response({
            'complaints': {
                'total': total_complaints,
                'pending': pending_complaints,
                'resolved': resolved_complaints,
                'resolution_rate': (resolved_complaints / total_complaints * 100) if total_complaints > 0 else 0
            },
            'enterprises': {
                'total': total_enterprises,
                'at_risk': at_risk_enterprises,
                'avg_compliance_score': round(avg_compliance, 2)
            },
            'inspections': {
                'total': total_inspections,
                'completed': completed_inspections,
                'completion_rate': (completed_inspections / total_inspections * 100) if total_inspections > 0 else 0
            },
            'mediations': {
                'total': total_mediations,
                'successful': successful_mediations,
                'success_rate': (successful_mediations / total_mediations * 100) if total_mediations > 0 else 0
            }
        })


class TrendsView(APIView):
    """Tendances et évolutions"""
    permission_classes = [IsInspecteur]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        # Évolution des plaintes par jour
        complaints_trend = Complaint.objects.filter(
            created_at__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        # Évolution inspections
        inspections_trend = InspectionRecord.objects.filter(
            created_at__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        return Response({
            'period_days': days,
            'complaints_trend': list(complaints_trend),
            'inspections_trend': list(inspections_trend)
        })


class ComplaintsByTypeView(APIView):
    """Répartition par type de plainte"""
    permission_classes = [IsInspecteur]

    def get(self, request):
        by_type = Complaint.objects.values('complaint_type').annotate(
            count=Count('id'),
            resolved=Count('id', filter=Q(status='RESOLVED')),
            pending=Count('id', filter=Q(status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']))
        ).order_by('-count')

        return Response({'complaints_by_type': list(by_type)})


class ComplaintsByRegionView(APIView):
    """Répartition par région"""
    permission_classes = [IsInspecteur]

    def get(self, request):
        by_region = Complaint.objects.values('inspection_zone__region').annotate(
            count=Count('id'),
            resolved=Count('id', filter=Q(status='RESOLVED'))
        ).order_by('-count')

        return Response({'complaints_by_region': list(by_region)})


class TopEnterprisesView(APIView):
    """Top entreprises par nombre de plaintes"""
    permission_classes = [IsInspecteur]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))

        top = Complaint.objects.values('employer_name').annotate(
            count=Count('id')
        ).order_by('-count')[:limit]

        return Response({'top_enterprises': list(top)})


class PerformanceMetricsView(APIView):
    """Métriques de performance"""
    permission_classes = [IsInspecteur]

    def get(self, request):
        # Délai moyen de résolution
        resolved = Complaint.objects.filter(status='RESOLVED', resolution_date__isnull=False)
        avg_days = 0
        if resolved.exists():
            total_days = sum([(c.resolution_date - c.created_at.date()).days for c in resolved])
            avg_days = total_days / resolved.count()

        # Taux de médiation réussie
        total_med = Mediation.objects.count()
        success_med = Mediation.objects.filter(outcome='AGREEMENT').count()

        # Conformité moyenne par secteur
        by_sector = Enterprise.objects.values('sector').annotate(
            avg_compliance=Avg('compliance_score'),
            count=Count('id')
        ).order_by('-avg_compliance')

        return Response({
            'average_resolution_days': round(avg_days, 1),
            'mediation_success_rate': (success_med / total_med * 100) if total_med > 0 else 0,
            'compliance_by_sector': list(by_sector)
        })


class ExecutiveDashboardView(APIView):
    """Dashboard pour les cadres (DG, Ministre)"""
    permission_classes = [IsDirecteurGeneral]

    def get(self, request):
        # KPIs principaux
        total_complaints = Complaint.objects.count()
        resolved_rate = (Complaint.objects.filter(status='RESOLVED').count() / total_complaints * 100) if total_complaints > 0 else 0

        # Alertes
        critical_enterprises = Enterprise.objects.filter(risk_level='CRITICAL').count()
        urgent_complaints = Complaint.objects.filter(priority='URGENT', status__in=['PENDING', 'ASSIGNED']).count()

        # 30 derniers jours
        last_30_days = timezone.now() - timedelta(days=30)
        new_complaints_30d = Complaint.objects.filter(created_at__gte=last_30_days).count()
        resolved_30d = Complaint.objects.filter(resolution_date__gte=last_30_days.date()).count()

        return Response({
            'kpis': {
                'total_complaints': total_complaints,
                'resolution_rate': round(resolved_rate, 1),
                'critical_enterprises': critical_enterprises,
                'urgent_complaints': urgent_complaints
            },
            'last_30_days': {
                'new_complaints': new_complaints_30d,
                'resolved_complaints': resolved_30d,
                'net_change': new_complaints_30d - resolved_30d
            },
            'alerts': {
                'critical_count': critical_enterprises + urgent_complaints,
                'needs_attention': urgent_complaints > 0 or critical_enterprises > 0
            }
        })

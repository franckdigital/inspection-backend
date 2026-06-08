from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import connection

from .models import Dashboard, Report, KPI, DataExport
from .serializers import DashboardSerializer, ReportSerializer, KPISerializer, DataExportSerializer


class DashboardViewSet(viewsets.ModelViewSet):
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Exécuter le rapport"""
        report = self.get_object()

        if report.query:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(report.query, report.query_params or {})
                    columns = [col[0] for col in cursor.description]
                    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

                    return Response({
                        'columns': columns,
                        'data': results,
                        'count': len(results)
                    })
                except Exception as e:
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        return Response({'error': 'No query configured'}, status=status.HTTP_400_BAD_REQUEST)


class KPIViewSet(viewsets.ModelViewSet):
    queryset = KPI.objects.all()
    serializer_class = KPISerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé de tous les KPIs"""
        kpis = KPI.objects.filter(is_active=True)

        summary = {
            'total': kpis.count(),
            'success': 0,
            'warning': 0,
            'critical': 0
        }

        for kpi in kpis:
            if kpi.current_value and kpi.target_value:
                if kpi.current_value >= kpi.target_value:
                    summary['success'] += 1
                elif kpi.warning_threshold and kpi.current_value >= kpi.warning_threshold:
                    summary['warning'] += 1
                else:
                    summary['critical'] += 1

        return Response(summary)


class DataExportViewSet(viewsets.ModelViewSet):
    queryset = DataExport.objects.all()
    serializer_class = DataExportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    @action(detail=False, methods=['post'])
    def request_export(self, request):
        """Demander un export"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        export = serializer.save(requested_by=request.user)

        # En production: lancer tâche Celery
        # export_task.delay(export.id)

        return Response({
            'message': 'Export lancé',
            'export_id': export.id
        })

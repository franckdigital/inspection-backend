from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import DashboardViewSet, ReportViewSet, KPIViewSet, DataExportViewSet

app_name = 'bi'

router = SimpleRouter()
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'kpis', KPIViewSet, basename='kpi')
router.register(r'exports', DataExportViewSet, basename='export')

urlpatterns = router.urls

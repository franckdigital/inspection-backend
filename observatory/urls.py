from django.urls import path
from .views import (
    NationalStatsView, TrendsView, ComplaintsByTypeView,
    ComplaintsByRegionView, TopEnterprisesView,
    PerformanceMetricsView, ExecutiveDashboardView
)

app_name = 'observatory'

urlpatterns = [
    path('national/', NationalStatsView.as_view(), name='national'),
    path('trends/', TrendsView.as_view(), name='trends'),
    path('complaints/by-type/', ComplaintsByTypeView.as_view(), name='by-type'),
    path('complaints/by-region/', ComplaintsByRegionView.as_view(), name='by-region'),
    path('enterprises/top/', TopEnterprisesView.as_view(), name='top-enterprises'),
    path('metrics/', PerformanceMetricsView.as_view(), name='metrics'),
    path('dashboard/executive/', ExecutiveDashboardView.as_view(), name='executive-dashboard'),
]

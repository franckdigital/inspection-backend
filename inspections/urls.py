from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import (
    InspectionZoneViewSet, InspectionRecordViewSet,
    CommuneViewSet, InspectorZoneAssignmentViewSet,
)

app_name = 'inspections'

router = SimpleRouter()
router.register(r'zones', InspectionZoneViewSet, basename='zone')
router.register(r'records', InspectionRecordViewSet, basename='record')
router.register(r'communes', CommuneViewSet, basename='commune')
router.register(r'zone-assignments', InspectorZoneAssignmentViewSet, basename='zone-assignment')

urlpatterns = router.urls

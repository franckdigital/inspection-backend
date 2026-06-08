from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import InspectionZoneViewSet, InspectionRecordViewSet

app_name = 'inspections'

router = SimpleRouter()
router.register(r'zones', InspectionZoneViewSet, basename='zone')
router.register(r'records', InspectionRecordViewSet, basename='record')

urlpatterns = router.urls

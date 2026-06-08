from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import (
    DomesticWorkerViewSet, DomesticEmployerViewSet, DomesticContractViewSet,
    TimeTrackingViewSet, MonthlyPayslipViewSet, LeaveRequestViewSet,
    OvertimeSessionViewSet, VoiceComplaintViewSet, FieldVisitViewSet,
)

app_name = 'domestic'

router = SimpleRouter()
router.register(r'workers', DomesticWorkerViewSet, basename='worker')
router.register(r'employers', DomesticEmployerViewSet, basename='employer')
router.register(r'contracts', DomesticContractViewSet, basename='contract')
router.register(r'tracking', TimeTrackingViewSet, basename='tracking')
router.register(r'payslips', MonthlyPayslipViewSet, basename='payslip')
router.register(r'leaves', LeaveRequestViewSet, basename='leave')
router.register(r'overtime', OvertimeSessionViewSet, basename='overtime')
router.register(r'voice-complaints', VoiceComplaintViewSet, basename='voice-complaint')
router.register(r'field-visits', FieldVisitViewSet, basename='field-visit')

urlpatterns = router.urls

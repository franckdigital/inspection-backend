from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import (
    WorkflowApprovalViewSet, EscalationViewSet,
    DelegationViewSet, ReassignmentHistoryViewSet
)

app_name = 'hierarchy'

router = SimpleRouter()
router.register(r'approvals', WorkflowApprovalViewSet, basename='approval')
router.register(r'escalations', EscalationViewSet, basename='escalation')
router.register(r'delegations', DelegationViewSet, basename='delegation')
router.register(r'reassignments', ReassignmentHistoryViewSet, basename='reassignment')

urlpatterns = router.urls

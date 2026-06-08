from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import MediationViewSet, MediationParticipantViewSet, AgreementViewSet

app_name = 'mediations'

router = SimpleRouter()
router.register(r'sessions', MediationViewSet, basename='session')
router.register(r'participants', MediationParticipantViewSet, basename='participant')
router.register(r'agreements', AgreementViewSet, basename='agreement')

urlpatterns = router.urls

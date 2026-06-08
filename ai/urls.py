from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import (
    ChatViewSet, DocumentAnalysisViewSet, ComplaintSimilarityViewSet,
    RiskPredictionViewSet, AbuseDetectionViewSet
)

app_name = 'ai'

router = SimpleRouter()
router.register(r'chat', ChatViewSet, basename='chat')
router.register(r'documents', DocumentAnalysisViewSet, basename='document')
router.register(r'similarity', ComplaintSimilarityViewSet, basename='similarity')
router.register(r'risks', RiskPredictionViewSet, basename='risk')
router.register(r'abuse', AbuseDetectionViewSet, basename='abuse')

urlpatterns = router.urls

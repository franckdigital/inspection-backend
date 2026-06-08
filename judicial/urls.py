from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import JudicialProcedureViewSet, HearingViewSet, JudicialDecisionViewSet

app_name = 'judicial'

router = SimpleRouter()
router.register(r'procedures', JudicialProcedureViewSet, basename='procedure')
router.register(r'hearings', HearingViewSet, basename='hearing')
router.register(r'decisions', JudicialDecisionViewSet, basename='decision')

urlpatterns = router.urls

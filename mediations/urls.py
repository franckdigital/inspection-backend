from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import MediationViewSet, MediationParticipantViewSet, AgreementViewSet

app_name = 'mediations'

router = SimpleRouter()
router.register(r'sessions',     MediationViewSet,            basename='session')
router.register(r'participants', MediationParticipantViewSet, basename='participant')
router.register(r'agreements',   AgreementViewSet,            basename='agreement')

# L'endpoint public d'accusé de réception est enregistré manuellement
# car il ne nécessite pas d'authentification JWT (lien dans email/SMS)
urlpatterns = router.urls + [
    path(
        'sessions/acknowledge/<str:token>/',
        MediationViewSet.as_view({'get': 'acknowledge_convocation'}),
        name='acknowledge-convocation',
    ),
]

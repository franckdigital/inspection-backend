from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import EnterpriseViewSet, EnterpriseBranchViewSet, EnterpriseDocumentViewSet, EnterpriseHistoryViewSet

app_name = 'enterprises'

router = SimpleRouter()
router.register(r'', EnterpriseViewSet, basename='enterprise')
router.register(r'branches', EnterpriseBranchViewSet, basename='branch')
router.register(r'documents', EnterpriseDocumentViewSet, basename='document')
router.register(r'history', EnterpriseHistoryViewSet, basename='history')

urlpatterns = router.urls

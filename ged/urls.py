from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import DocumentCategoryViewSet, DocumentViewSet, DocumentVersionViewSet, DocumentAccessViewSet, ArchiveViewSet

app_name = 'ged'

router = SimpleRouter()
router.register(r'categories', DocumentCategoryViewSet, basename='category')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'versions', DocumentVersionViewSet, basename='version')
router.register(r'access', DocumentAccessViewSet, basename='access')
router.register(r'archives', ArchiveViewSet, basename='archive')

urlpatterns = router.urls

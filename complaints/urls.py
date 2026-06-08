from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import ComplaintViewSet, ComplaintNotificationViewSet

app_name = 'complaints'

router = SimpleRouter()
router.register(r'', ComplaintViewSet, basename='complaint')
router.register(r'notifications', ComplaintNotificationViewSet, basename='notification')

urlpatterns = router.urls

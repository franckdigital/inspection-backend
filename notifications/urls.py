from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import EmailTemplateViewSet, EmailLogViewSet, SMSTemplateViewSet, SMSLogViewSet

app_name = 'notifications'

router = SimpleRouter()
router.register(r'email/templates', EmailTemplateViewSet, basename='email-template')
router.register(r'email/logs', EmailLogViewSet, basename='email-log')
router.register(r'sms/templates', SMSTemplateViewSet, basename='sms-template')
router.register(r'sms/logs', SMSLogViewSet, basename='sms-log')

urlpatterns = router.urls

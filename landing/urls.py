from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import admin_views

router = DefaultRouter()
router.register('news', views.NewsArticleViewSet, basename='news')
router.register('ai-responses', admin_views.AIKeywordResponseViewSet, basename='ai-responses')
router.register('faqs', admin_views.FAQViewSet, basename='faqs')
router.register('contact-messages', admin_views.ContactMessageViewSet, basename='contact-messages')
router.register('testimonials', admin_views.TestimonialViewSet, basename='testimonials')
router.register('campaigns', admin_views.CampaignViewSet, basename='campaigns-admin')
router.register('offices', admin_views.InspectionOfficeViewSet, basename='offices')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Public stats
    path('stats/', views.public_stats, name='public-stats'),

    # FAQ
    path('faq/', views.faq_list, name='faq-list'),

    # Resources
    path('resources/', views.resources_list, name='resources-list'),
    path('resources/<int:pk>/download/', views.resource_download, name='resource-download'),

    # Testimonials
    path('testimonials/', views.testimonials_list, name='testimonials-list'),

    # Campaigns
    path('campaigns/', views.campaigns_list, name='campaigns-list'),

    # Press releases
    path('press/', views.press_releases_list, name='press-releases-list'),

    # Contact
    path('contact/', views.contact_submit, name='contact-submit'),

    # Inspection offices
    path('inspection-offices/', views.inspection_offices_list, name='inspection-offices-list'),

    # AI Assistant
    path('ai-assistant/', views.ai_assistant, name='ai-assistant'),
]

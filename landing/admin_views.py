"""
ViewSets pour l'administration du contenu du site vitrine (LOT 0)
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    AIKeywordResponse, FAQ, ContactMessage,
    Testimonial, Campaign, InspectionOffice
)
from .serializers import (
    FAQSerializer, ContactMessageSerializer,
    TestimonialSerializer, CampaignSerializer,
    InspectionOfficeSerializer
)


class AIKeywordResponseSerializer:
    """Serializer temporaire pour AIKeywordResponse"""
    pass  # TODO: Créer le vrai serializer


# ===== VIEWSETS ADMIN =====

class AIKeywordResponseViewSet(viewsets.ModelViewSet):
    """CRUD complet pour gérer les réponses de l'assistant IA"""
    queryset = AIKeywordResponse.objects.all().order_by('priority')
    permission_classes = [permissions.IsAuthenticated]  # Temporairement, à changer en IsAdminUser

    def get_serializer_class(self):
        # Retourner les données directement en JSON pour le moment
        return None

    def list(self, request):
        queryset = self.get_queryset()
        data = [{
            'id': obj.id,
            'keyword': obj.keyword,
            'question_example': obj.question_example,
            'response': obj.response,
            'priority': obj.priority,
            'is_active': obj.is_active,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
        } for obj in queryset]
        return Response({'results': data, 'count': len(data)})

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return Response({
            'id': obj.id,
            'keyword': obj.keyword,
            'question_example': obj.question_example,
            'response': obj.response,
            'priority': obj.priority,
            'is_active': obj.is_active,
        })


class FAQViewSet(viewsets.ModelViewSet):
    """CRUD complet pour gérer les FAQs"""
    queryset = FAQ.objects.all().order_by('category', 'order')
    serializer_class = FAQSerializer
    permission_classes = [permissions.IsAuthenticated]


class ContactMessageViewSet(viewsets.ModelViewSet):
    """CRUD complet pour gérer les messages de contact"""
    queryset = ContactMessage.objects.all().order_by('-created_at')
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marquer un message comme lu"""
        message = self.get_object()
        message.is_read = True
        message.save()
        return Response({'status': 'Message marqué comme lu'})


class TestimonialViewSet(viewsets.ModelViewSet):
    """CRUD complet pour gérer les témoignages"""
    queryset = Testimonial.objects.all().order_by('-published_at')
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.IsAuthenticated]


class CampaignViewSet(viewsets.ModelViewSet):
    """CRUD complet pour gérer les campagnes"""
    queryset = Campaign.objects.all().order_by('-start_date')
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]


class InspectionOfficeViewSet(viewsets.ModelViewSet):
    """CRUD complet pour gérer les bureaux d'inspection"""
    queryset = InspectionOffice.objects.all().order_by('region', 'name')
    serializer_class = InspectionOfficeSerializer
    permission_classes = [permissions.IsAuthenticated]

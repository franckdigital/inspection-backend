from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    NewsArticle, FAQ, ResourceDocument, Testimonial,
    Campaign, PressRelease, ContactMessage, InspectionOffice,
    AIKeywordResponse
)
from .serializers import (
    NewsArticleSerializer, FAQSerializer, ResourceDocumentSerializer,
    TestimonialSerializer, CampaignSerializer, PressReleaseSerializer,
    ContactMessageSerializer, InspectionOfficeSerializer, PublicStatsSerializer
)

from users.models import User
from enterprises.models import Enterprise
from complaints.models import Complaint
# Note: Using try-except for inspections count in case model changes
from mediations.models import Mediation


# ===== PUBLIC STATS =====

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_stats(request):
    """Statistiques publiques pour la page d accueil"""

    # Compter les utilisateurs (travailleurs)
    total_workers = User.objects.filter(user_type='EMPLOYEE').count()

    # Compter les entreprises
    total_enterprises = Enterprise.objects.count()

    # Compter les plaintes
    total_complaints = Complaint.objects.count()
    complaints_resolved = Complaint.objects.filter(
        status__in=['RESOLVED', 'CLOSED']
    ).count()

    # Compter les inspections
    try:
        from inspections.models import InspectionRecord
        total_inspections = InspectionRecord.objects.count()
    except:
        total_inspections = 0

    # Compter les m�diations
    total_mediations = Mediation.objects.count()

    # Calculer le taux de satisfaction (bas� sur les plaintes r�solues)
    if total_complaints > 0:
        satisfaction_rate = round((complaints_resolved / total_complaints) * 100, 1)
    else:
        satisfaction_rate = 0.0

    stats = {
        'total_workers': total_workers,
        'total_enterprises': total_enterprises,
        'total_complaints': total_complaints,
        'total_inspections': total_inspections,
        'total_mediations': total_mediations,
        'complaints_resolved': complaints_resolved,
        'satisfaction_rate': satisfaction_rate,
    }

    serializer = PublicStatsSerializer(stats)
    return Response(serializer.data)


# ===== NEWS ARTICLES =====

class NewsArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """Articles d actualit� (lecture seule pour le public)"""
    queryset = NewsArticle.objects.filter(published_at__lte=timezone.now())
    serializer_class = NewsArticleSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        """Incr�menter le compteur de vues"""
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# ===== FAQ =====

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def faq_list(request):
    """Liste des FAQs actives"""
    faqs = FAQ.objects.filter(is_active=True)
    serializer = FAQSerializer(faqs, many=True)
    return Response(serializer.data)


# ===== RESOURCES =====

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def resources_list(request):
    """Liste des ressources actives"""
    resources = ResourceDocument.objects.filter(is_active=True)
    category = request.query_params.get('category', None)
    if category:
        resources = resources.filter(category=category)
    serializer = ResourceDocumentSerializer(resources, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def resource_download(request, pk):
    """T�l�charger une ressource et incr�menter le compteur"""
    try:
        resource = ResourceDocument.objects.get(pk=pk, is_active=True)
        resource.downloads += 1
        resource.save(update_fields=['downloads'])
        return Response({'file_url': resource.file.url})
    except ResourceDocument.DoesNotExist:
        return Response(
            {'error': 'Ressource non trouv�e'},
            status=status.HTTP_404_NOT_FOUND
        )


# ===== TESTIMONIALS =====

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def testimonials_list(request):
    """Liste des t�moignages approuv�s"""
    testimonials = Testimonial.objects.filter(is_approved=True)
    serializer = TestimonialSerializer(testimonials, many=True)
    return Response(serializer.data)


# ===== CAMPAIGNS =====

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def campaigns_list(request):
    """Liste des campagnes actives"""
    now = timezone.now().date()
    campaigns = Campaign.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    )
    serializer = CampaignSerializer(campaigns, many=True)
    return Response(serializer.data)


# ===== PRESS RELEASES =====

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def press_releases_list(request):
    """Liste des communiqu�s de presse actifs"""
    press_releases = PressRelease.objects.filter(is_active=True)
    serializer = PressReleaseSerializer(press_releases, many=True)
    return Response(serializer.data)


# ===== CONTACT =====

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def contact_submit(request):
    """Soumettre un message de contact"""
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Votre message a �t� envoy� avec succ�s. Nous vous r�pondrons dans les plus brefs d�lais.'},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===== INSPECTION OFFICES =====

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def inspection_offices_list(request):
    """Liste des bureaux d inspection actifs"""
    offices = InspectionOffice.objects.filter(is_active=True)
    region = request.query_params.get('region', None)
    if region:
        offices = offices.filter(region=region)
    serializer = InspectionOfficeSerializer(offices, many=True)
    return Response(serializer.data)


# ===== AI ASSISTANT =====

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def ai_assistant(request):
    """Assistant IA pour repondre aux questions base sur mots-cles parametrables"""
    question = request.data.get('question', '')

    if not question:
        return Response(
            {'error': 'Question requise'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Recuperer toutes les reponses actives depuis la BD, triees par priorite
    keyword_responses = AIKeywordResponse.objects.filter(is_active=True).order_by('priority')

    # Chercher une reponse basee sur les mots-cles
    answer = None
    question_lower = question.lower()

    for kr in keyword_responses:
        if kr.keyword.lower() in question_lower:
            answer = kr.response
            break

    # Reponse par defaut si aucun mot-cle ne correspond
    if not answer:
        # Essayer de trouver une reponse par defaut dans la BD
        default_response = AIKeywordResponse.objects.filter(
            keyword__iexact='default',
            is_active=True
        ).first()

        if default_response:
            answer = default_response.response
        else:
            # Fallback si aucune reponse par defaut configuree
            answer = "Merci pour votre question. Pour des informations precises sur le droit du travail en Cote d'Ivoire, je vous recommande de consulter notre centre de ressources ou de contacter directement l'inspection du travail. Vous pouvez egalement deposer une plainte en ligne si vous rencontrez un probleme specifique avec votre employeur."

    return Response({'answer': answer})


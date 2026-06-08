from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
import uuid

from .models import ChatConversation, ChatMessage, DocumentAnalysis, ComplaintSimilarity, RiskPrediction, AbuseDetection
from .serializers import (
    ChatConversationSerializer, ChatMessageSerializer, ChatRequestSerializer,
    DocumentAnalysisSerializer, ComplaintSimilaritySerializer,
    RiskPredictionSerializer, AbuseDetectionSerializer
)
from .services import ChatbotService, OCRService, SimilarityService, RiskPredictionService, AbuseDetectionService


class ChatViewSet(viewsets.ModelViewSet):
    queryset = ChatConversation.objects.all()
    serializer_class = ChatConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatConversation.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """Envoyer un message au chatbot"""
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id') or str(uuid.uuid4())

        # Récupérer ou créer conversation
        conversation, created = ChatConversation.objects.get_or_create(
            user=request.user,
            session_id=session_id,
            is_active=True,
            defaults={'initial_topic': user_message[:255]}
        )

        # Sauvegarder message utilisateur
        ChatMessage.objects.create(
            conversation=conversation,
            role='USER',
            content=user_message
        )

        # Générer réponse IA
        bot_response = ChatbotService.get_response(user_message)

        # Sauvegarder réponse
        ChatMessage.objects.create(
            conversation=conversation,
            role='ASSISTANT',
            content=bot_response['response'],
            confidence_score=bot_response.get('confidence', 0.5),
            model_used='simulation-v1'
        )

        return Response({
            'session_id': session_id,
            'response': bot_response['response'],
            'confidence': bot_response.get('confidence'),
            'topic': bot_response.get('topic')
        })


class DocumentAnalysisViewSet(viewsets.ModelViewSet):
    queryset = DocumentAnalysis.objects.all()
    serializer_class = DocumentAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        analysis = serializer.save(uploaded_by=self.request.user, status='PROCESSING')

        # Lancer OCR et analyse (simulation)
        ocr_result = OCRService.extract_text_from_image(analysis.document_file.path)
        analysis.extracted_text = ocr_result['text']
        analysis.ocr_confidence = ocr_result['confidence']
        analysis.language_detected = ocr_result['language']

        # Analyse IA du contrat
        if analysis.document_type == 'CONTRACT':
            ai_analysis = OCRService.analyze_contract(analysis.extracted_text)
            analysis.ai_summary = ai_analysis['summary']
            analysis.detected_issues = ai_analysis['issues']
            analysis.key_clauses = ai_analysis['clauses']

        analysis.status = 'COMPLETED'
        analysis.completed_at = timezone.now()
        analysis.save()


class ComplaintSimilarityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ComplaintSimilarity.objects.all()
    serializer_class = ComplaintSimilaritySerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def find_similar(self, request):
        """Trouver les plaintes similaires"""
        from complaints.models import Complaint

        complaint_id = request.data.get('complaint_id')
        try:
            complaint = Complaint.objects.get(id=complaint_id)
        except Complaint.DoesNotExist:
            return Response({'error': 'Plainte non trouvée'}, status=status.HTTP_404_NOT_FOUND)

        similar = SimilarityService.find_similar_complaints(complaint)

        return Response({
            'complaint_number': complaint.complaint_number,
            'similar_count': len(similar),
            'similar_complaints': similar
        })


class RiskPredictionViewSet(viewsets.ModelViewSet):
    queryset = RiskPrediction.objects.all()
    serializer_class = RiskPredictionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def predict(self, request):
        """Prédire les risques pour une entreprise"""
        from enterprises.models import Enterprise

        enterprise_id = request.data.get('enterprise_id')
        try:
            enterprise = Enterprise.objects.get(id=enterprise_id)
        except Enterprise.DoesNotExist:
            return Response({'error': 'Entreprise non trouvée'}, status=status.HTTP_404_NOT_FOUND)

        risks = RiskPredictionService.predict_enterprise_risk(enterprise)

        # Sauvegarder les prédictions
        for risk_data in risks:
            RiskPrediction.objects.create(
                enterprise=enterprise,
                risk_type=risk_data['type'],
                risk_level=risk_data['level'],
                probability=risk_data['probability'],
                contributing_factors=risk_data['factors'],
                model_version='v1.0'
            )

        return Response({
            'enterprise_name': enterprise.name,
            'risks_count': len(risks),
            'risks': risks
        })


class AbuseDetectionViewSet(viewsets.ModelViewSet):
    queryset = AbuseDetection.objects.all()
    serializer_class = AbuseDetectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def analyze_complaint(self, request):
        """Analyser une plainte pour détecter les abus"""
        from complaints.models import Complaint

        complaint_id = request.data.get('complaint_id')
        try:
            complaint = Complaint.objects.get(id=complaint_id)
        except Complaint.DoesNotExist:
            return Response({'error': 'Plainte non trouvée'}, status=status.HTTP_404_NOT_FOUND)

        complaint_text = f"{complaint.subject} {complaint.description}"
        detections = AbuseDetectionService.detect_abuse(complaint_text)

        # Sauvegarder les détections
        for detection in detections:
            AbuseDetection.objects.create(
                complaint=complaint,
                abuse_type=detection['abuse_type'],
                detection_score=detection['score'],
                evidence_keywords=detection['keywords'],
                urgency_level=detection['urgency'],
                recommended_actions=f"Enquête urgente recommandée pour {detection['abuse_type']}"
            )

        return Response({
            'complaint_number': complaint.complaint_number,
            'detections_count': len(detections),
            'detections': detections
        })

"""Services IA - Simulation sans API externe pour démonstration"""

import re
import random

# NOTE: Installer scikit-learn pour production: pip install scikit-learn
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity


class ChatbotService:
    """Service de chatbot juridique (simulation)"""

    LABOR_KEYWORDS = {
        'licenciement': 'procédure de licenciement',
        'salaire': 'droits salariaux',
        'congé': 'congés légaux',
        'harcèlement': 'harcèlement au travail',
        'heures supplémentaires': 'heures supplémentaires',
        'contrat': 'contrat de travail',
        'démission': 'procédure de démission',
        'accident': 'accident de travail',
    }

    @staticmethod
    def get_response(user_message, conversation_history=None):
        """
        Génère une réponse du chatbot

        En production, utiliser OpenAI API ou Claude API:
        import openai
        response = openai.ChatCompletion.create(...)
        """
        user_message_lower = user_message.lower()

        # Détection de sujet
        detected_topic = None
        for keyword, topic in ChatbotService.LABOR_KEYWORDS.items():
            if keyword in user_message_lower:
                detected_topic = topic
                break

        # Réponses simulées basiques
        if 'bonjour' in user_message_lower or 'salut' in user_message_lower:
            return {
                'response': "Bonjour ! Je suis l'assistant juridique du Ministère du Travail. Comment puis-je vous aider aujourd'hui ?",
                'confidence': 1.0,
                'topic': 'greeting'
            }

        if detected_topic:
            responses = {
                'procédure de licenciement': "Le licenciement doit respecter une procédure légale. L'employeur doit convoquer le salarié à un entretien préalable, notifier par écrit les motifs, et respecter un préavis. Souhaitez-vous déposer une plainte pour licenciement abusif ?",
                'droits salariaux': "Tous les salaires doivent être payés au plus tard le 8 du mois suivant. Le salaire minimum est de 75 000 CDF. Avez-vous des retards de paiement ?",
                'congés légaux': "Vous avez droit à 15 jours de congés payés par an après un an de service. Les congés maladie nécessitent un certificat médical.",
                'harcèlement au travail': "Le harcèlement au travail est strictement interdit. Vous pouvez déposer une plainte confidentielle. Souhaitez-vous être mis en contact avec un inspecteur ?",
            }
            return {
                'response': responses.get(detected_topic, "Je peux vous aider avec des questions sur le droit du travail."),
                'confidence': 0.85,
                'topic': detected_topic
            }

        # Réponse par défaut
        return {
            'response': "Je peux vous renseigner sur : les licenciements, les salaires, les congés, le harcèlement, les heures supplémentaires, et les contrats de travail. Quelle est votre question ?",
            'confidence': 0.5,
            'topic': 'general'
        }


class OCRService:
    """Service OCR de documents (simulation)"""

    @staticmethod
    def extract_text_from_image(image_path):
        """
        Extrait le texte d'une image

        En production, utiliser Tesseract ou Cloud Vision API:
        import pytesseract
        from PIL import Image
        text = pytesseract.image_to_string(Image.open(image_path))
        """
        # Simulation
        return {
            'text': "Ceci est un texte extrait simulé du document.\nContrat de travail\nSalaire: 150000 CDF\nDate début: 01/01/2026",
            'confidence': 0.92,
            'language': 'fr'
        }

    @staticmethod
    def analyze_contract(text):
        """Analyse un contrat de travail"""
        issues = []
        clauses = []

        # Détection basique de problèmes
        if 'salaire' not in text.lower():
            issues.append("Salaire non mentionné")
        if 'durée' not in text.lower() and 'période' not in text.lower():
            issues.append("Durée du contrat non précisée")

        # Extraction de clauses (simulation)
        if 'CDF' in text or 'salaire' in text.lower():
            clauses.append("Clause salariale détectée")
        if 'congé' in text.lower():
            clauses.append("Clause de congés détectée")

        return {
            'issues': issues,
            'clauses': clauses,
            'summary': "Contrat analysé avec {} clause(s) et {} problème(s) potentiel(s)".format(
                len(clauses), len(issues)
            )
        }


class SimilarityService:
    """Service de calcul de similarité entre plaintes"""

    @staticmethod
    def calculate_text_similarity(text1, text2):
        """Calcule la similarité textuelle (simulation simple)"""
        if not text1 or not text2:
            return 0.0

        # Simulation simple basée sur mots communs
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        common = words1.intersection(words2)
        total = words1.union(words2)

        return len(common) / len(total) if total else 0.0

    @staticmethod
    def find_similar_complaints(complaint, limit=5):
        """Trouve les plaintes similaires"""
        from complaints.models import Complaint

        similar = []
        target_text = f"{complaint.subject} {complaint.description}"

        # Filtrer par type d'abord
        candidates = Complaint.objects.filter(
            complaint_type=complaint.complaint_type
        ).exclude(id=complaint.id)[:50]  # Limiter pour performance

        for candidate in candidates:
            candidate_text = f"{candidate.subject} {candidate.description}"
            similarity = SimilarityService.calculate_text_similarity(target_text, candidate_text)

            if similarity > 0.3:  # Seuil de similarité
                similar.append({
                    'complaint': candidate,
                    'similarity_score': similarity,
                    'type_match': True,
                    'employer_match': complaint.employer_name == candidate.employer_name
                })

        # Trier par score
        similar.sort(key=lambda x: x['similarity_score'], reverse=True)

        return similar[:limit]


class RiskPredictionService:
    """Service de prédiction de risques sociaux"""

    @staticmethod
    def predict_enterprise_risk(enterprise):
        """Prédit les risques pour une entreprise"""
        from complaints.models import Complaint

        # Analyser historique des plaintes
        complaints_count = Complaint.objects.filter(
            employer_name__icontains=enterprise.name
        ).count()

        recent_complaints = Complaint.objects.filter(
            employer_name__icontains=enterprise.name,
            created_at__gte='2026-01-01'
        ).count()

        # Logique simple de prédiction
        risks = []

        # Risque de grève
        if recent_complaints > 5:
            risks.append({
                'type': 'STRIKE',
                'level': 'HIGH' if recent_complaints > 10 else 'MEDIUM',
                'probability': min(recent_complaints * 0.1, 0.9),
                'factors': [
                    f'{recent_complaints} plaintes récentes',
                    'Augmentation des tensions sociales'
                ]
            })

        # Risque de litige
        if complaints_count > 3:
            risks.append({
                'type': 'LABOR_DISPUTE',
                'level': 'MEDIUM',
                'probability': min(complaints_count * 0.05, 0.7),
                'factors': [
                    f'{complaints_count} plaintes au total',
                    'Historique de conflits'
                ]
            })

        # Score de conformité faible
        if enterprise.compliance_score < 50:
            risks.append({
                'type': 'SOCIAL_UNREST',
                'level': 'HIGH',
                'probability': (100 - enterprise.compliance_score) / 100,
                'factors': [
                    f'Score de conformité faible ({enterprise.compliance_score})',
                    'Non-respect des normes'
                ]
            })

        return risks


class AbuseDetectionService:
    """Service de détection d'abus"""

    ABUSE_KEYWORDS = {
        'HARASSMENT': ['harcèlement', 'insulte', 'menace', 'intimidation', 'humiliation'],
        'DISCRIMINATION': ['discrimination', 'racisme', 'sexisme', 'âge', 'handicap'],
        'CHILD_LABOR': ['mineur', 'enfant', 'jeune', 'moins de 18'],
        'FORCED_LABOR': ['forcé', 'contraint', 'obligé', 'menace', 'retenu'],
        'UNSAFE_CONDITIONS': ['danger', 'accident', 'sécurité', 'risque', 'blessure'],
        'WAGE_THEFT': ['salaire impayé', 'retard paiement', 'non payé', 'vol salaire'],
    }

    @staticmethod
    def detect_abuse(complaint_text):
        """Détecte les abus potentiels dans une plainte"""
        complaint_lower = complaint_text.lower()
        detections = []

        for abuse_type, keywords in AbuseDetectionService.ABUSE_KEYWORDS.items():
            found_keywords = []
            for keyword in keywords:
                if keyword in complaint_lower:
                    found_keywords.append(keyword)

            if found_keywords:
                score = min(len(found_keywords) * 0.25, 1.0)
                urgency = 'URGENT' if score > 0.7 else ('HIGH' if score > 0.5 else 'MEDIUM')

                detections.append({
                    'abuse_type': abuse_type,
                    'score': score,
                    'keywords': found_keywords,
                    'urgency': urgency
                })

        return sorted(detections, key=lambda x: x['score'], reverse=True)

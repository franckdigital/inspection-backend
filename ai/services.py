"""
Services IA — Plateforme e-Inspection du Travail Côte d'Ivoire
ChatbotService : Claude API (Anthropic) avec fallback simulation si clé absente.
"""

import re
from django.conf import settings

# ── Système Prompt Droit du Travail CI ───────────────────────────────────────

_SYSTEM_PROMPT = """Tu es l'assistant juridique officiel du Ministère du Travail et de la Protection Sociale
de Côte d'Ivoire. Tu aides les travailleurs, employés de maison et employeurs à comprendre leurs droits
et obligations en vertu du Code du Travail ivoirien (Loi n° 2015-532 du 20 juillet 2015).

Règles :
- Réponds toujours en français clair et accessible.
- Cite les articles du Code du Travail CI lorsque c'est pertinent.
- Ne donne pas de conseil juridique personnalisé ; oriente vers un inspecteur pour les cas complexes.
- En cas de harcèlement, discrimination ou travail forcé, propose immédiatement de déposer une plainte.
- SMIG actuel : 75 000 FCFA/mois. Heure supplémentaire : +15% (50 premières) puis +50%.
- Préavis licenciement : 1 mois (moins d'un an), 2 mois (1-5 ans), 3 mois (plus de 5 ans).
- Congés payés : 2,5 jours par mois travaillé (30 jours/an maximum).
"""


class ChatbotService:
    """Chatbot juridique — Claude API ou fallback simulation."""

    # ── Réponses de secours (simulation) ─────────────────────────────────────

    _FALLBACK_TOPICS = {
        'licenciement': (
            "Un licenciement doit suivre une procédure légale : convocation écrite à entretien "
            "préalable, notification des motifs, puis respect du préavis (Art. 18.1 Code du Travail CI). "
            "En cas de licenciement abusif, vous pouvez déposer une plainte auprès de l'Inspection."
        ),
        'salaire': (
            "Le SMIG est fixé à 75 000 FCFA/mois. Les salaires doivent être versés au plus tard "
            "le 8 du mois suivant. Tout retard de plus de 8 jours peut faire l'objet d'une plainte "
            "(Art. 31.3 Code du Travail CI)."
        ),
        'congé': (
            "Vous avez droit à 2,5 jours de congés payés par mois travaillé (30 jours/an). "
            "L'employeur doit notifier les dates 30 jours à l'avance (Art. 25.1 Code du Travail CI)."
        ),
        'harcèlement': (
            "Le harcèlement moral et sexuel est interdit et constitue une faute grave. "
            "Vous pouvez déposer une plainte confidentielle — un inspecteur vous contactera sous 72h. "
            "Souhaitez-vous être mis en relation avec un inspecteur ?"
        ),
        'heures supplémentaires': (
            "Les heures supplémentaires sont majorées de +15% pour les 8 premières heures "
            "au-delà de 40h/semaine, puis +50% au-delà (Art. 21.2). "
            "La durée maximale est de 60h/semaine."
        ),
        'contrat': (
            "Le contrat de travail peut être à durée déterminée (CDD, max 2 ans renouvelable une fois) "
            "ou indéterminée (CDI). Tout contrat doit préciser le poste, le salaire et la durée "
            "(Art. 14.1 Code du Travail CI)."
        ),
        'accident': (
            "En cas d'accident de travail, prévenez immédiatement l'employeur (24h). "
            "Vous avez droit à la prise en charge des soins médicaux par la CNPS et "
            "à des indemnités journalières si vous êtes en incapacité (Art. 33.1)."
        ),
    }

    @staticmethod
    def get_response(user_message: str, conversation_history=None):
        """
        Envoie le message à Claude API si ANTHROPIC_API_KEY est configurée,
        sinon utilise la simulation par correspondance de mots-clés.
        """
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', '') or getattr(settings, 'OPENAI_API_KEY', '')

        if api_key and api_key.startswith('sk-ant-'):
            return ChatbotService._call_claude(user_message, conversation_history, api_key)
        elif api_key and api_key.startswith('sk-'):
            return ChatbotService._call_openai(user_message, conversation_history, api_key)
        else:
            return ChatbotService._fallback(user_message)

    # ── Claude (Anthropic) ────────────────────────────────────────────────────

    @staticmethod
    def _call_claude(message: str, history, api_key: str):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            messages = []
            for turn in (history or []):
                if turn.get('role') in ('user', 'assistant'):
                    messages.append({'role': turn['role'], 'content': turn['content']})
            messages.append({'role': 'user', 'content': message})

            response = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=512,
                system=_SYSTEM_PROMPT,
                messages=messages,
            )
            text = response.content[0].text
            return {'response': text, 'confidence': 0.95, 'topic': 'llm', 'provider': 'anthropic'}
        except Exception as exc:
            return ChatbotService._fallback(message, error=str(exc))

    # ── OpenAI ────────────────────────────────────────────────────────────────

    @staticmethod
    def _call_openai(message: str, history, api_key: str):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            messages = [{'role': 'system', 'content': _SYSTEM_PROMPT}]
            for turn in (history or []):
                if turn.get('role') in ('user', 'assistant'):
                    messages.append({'role': turn['role'], 'content': turn['content']})
            messages.append({'role': 'user', 'content': message})

            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=messages,
                max_tokens=512,
                temperature=0.3,
            )
            text = resp.choices[0].message.content
            return {'response': text, 'confidence': 0.95, 'topic': 'llm', 'provider': 'openai'}
        except Exception as exc:
            return ChatbotService._fallback(message, error=str(exc))

    # ── Fallback simulation ───────────────────────────────────────────────────

    @staticmethod
    def _fallback(message: str, error: str = None):
        msg_lower = message.lower()

        if any(w in msg_lower for w in ('bonjour', 'salut', 'bonsoir', 'hello')):
            return {
                'response': (
                    "Bonjour ! Je suis l'assistant juridique du Ministère du Travail de Côte d'Ivoire. "
                    "Je peux vous renseigner sur vos droits et obligations. Comment puis-je vous aider ?"
                ),
                'confidence': 1.0, 'topic': 'greeting', 'provider': 'fallback'
            }

        for keyword, response_text in ChatbotService._FALLBACK_TOPICS.items():
            if keyword in msg_lower:
                return {'response': response_text, 'confidence': 0.80, 'topic': keyword, 'provider': 'fallback'}

        return {
            'response': (
                "Je peux vous renseigner sur : les licenciements, les salaires, les congés, "
                "le harcèlement, les heures supplémentaires, les contrats de travail et les accidents. "
                "Quelle est votre question ?"
            ),
            'confidence': 0.5, 'topic': 'general', 'provider': 'fallback'
        }


class OCRService:
    """Service OCR — extraction de texte depuis documents."""

    @staticmethod
    def extract_text_from_image(image_path: str):
        try:
            import pytesseract
            from PIL import Image
            text = pytesseract.image_to_string(Image.open(image_path), lang='fra')
            return {'text': text, 'confidence': 0.88, 'language': 'fr'}
        except ImportError:
            return {
                'text': "[OCR non disponible — installer pytesseract et Pillow]",
                'confidence': 0.0, 'language': 'fr'
            }
        except Exception as exc:
            return {'text': '', 'confidence': 0.0, 'error': str(exc)}

    @staticmethod
    def analyze_contract(text: str):
        issues = []
        clauses = []
        text_lower = text.lower()

        if 'salaire' not in text_lower and 'rémunération' not in text_lower:
            issues.append("Salaire/rémunération non mentionné")
        if 'durée' not in text_lower and 'période' not in text_lower:
            issues.append("Durée du contrat non précisée")
        if 'poste' not in text_lower and 'fonction' not in text_lower:
            issues.append("Poste ou fonction non précisé")

        if re.search(r'(fcfa|cfa|salaire|rémunération)', text_lower):
            clauses.append("Clause salariale détectée")
        if 'congé' in text_lower:
            clauses.append("Clause de congés détectée")
        if 'préavis' in text_lower:
            clauses.append("Clause de préavis détectée")

        return {
            'issues': issues,
            'clauses': clauses,
            'summary': f"Contrat analysé : {len(clauses)} clause(s) détectée(s), {len(issues)} anomalie(s)."
        }


class SimilarityService:
    """Similarité entre plaintes — Jaccard sur sac de mots."""

    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)

    @staticmethod
    def find_similar_complaints(complaint, limit: int = 5):
        from complaints.models import Complaint

        target_text = f"{complaint.subject} {complaint.description}"
        candidates = Complaint.objects.filter(
            complaint_type=complaint.complaint_type
        ).exclude(id=complaint.id)[:50]

        scored = []
        for c in candidates:
            score = SimilarityService.calculate_text_similarity(
                target_text, f"{c.subject} {c.description}"
            )
            if score > 0.25:
                scored.append({
                    'complaint': c,
                    'similarity_score': round(score, 3),
                    'type_match': True,
                    'employer_match': complaint.employer_name == c.employer_name,
                })

        return sorted(scored, key=lambda x: x['similarity_score'], reverse=True)[:limit]


class RiskPredictionService:
    """Prédiction de risques sociaux pour une entreprise."""

    @staticmethod
    def predict_enterprise_risk(enterprise):
        from complaints.models import Complaint
        from django.utils import timezone
        from datetime import timedelta

        six_months_ago = timezone.now() - timedelta(days=180)
        total_complaints = Complaint.objects.filter(employer_name__icontains=enterprise.name).count()
        recent_complaints = Complaint.objects.filter(
            employer_name__icontains=enterprise.name,
            created_at__gte=six_months_ago
        ).count()

        risks = []

        if recent_complaints > 5:
            risks.append({
                'type': 'STRIKE',
                'level': 'HIGH' if recent_complaints > 10 else 'MEDIUM',
                'probability': min(recent_complaints * 0.08, 0.90),
                'factors': [f'{recent_complaints} plaintes sur 6 mois', 'Tensions sociales croissantes'],
            })

        if total_complaints > 3:
            risks.append({
                'type': 'LABOR_DISPUTE',
                'level': 'MEDIUM',
                'probability': min(total_complaints * 0.05, 0.70),
                'factors': [f'{total_complaints} plaintes au total', 'Historique de conflits'],
            })

        if enterprise.compliance_score < 50:
            risks.append({
                'type': 'NON_COMPLIANCE',
                'level': 'HIGH',
                'probability': (100 - enterprise.compliance_score) / 100,
                'factors': [f'Score conformité : {enterprise.compliance_score}/100'],
            })

        return risks


class AbuseDetectionService:
    """Détection de signaux d'alerte dans les textes de plaintes."""

    ABUSE_KEYWORDS = {
        'HARASSMENT':        ['harcèlement', 'insulte', 'menace', 'intimidation', 'humiliation'],
        'DISCRIMINATION':    ['discrimination', 'racisme', 'sexisme', 'handicap'],
        'CHILD_LABOR':       ['mineur', 'enfant', 'moins de 18', 'jeune travailleur'],
        'FORCED_LABOR':      ['forcé', 'contraint', 'obligé', 'retenu', 'travail forcé'],
        'UNSAFE_CONDITIONS': ['danger', 'accident', 'sécurité', 'risque', 'blessure', 'EPI'],
        'WAGE_THEFT':        ['salaire impayé', 'retard paiement', 'non payé', 'retenue illégale'],
    }

    @staticmethod
    def detect_abuse(complaint_text: str):
        text_lower = complaint_text.lower()
        detections = []

        for abuse_type, keywords in AbuseDetectionService.ABUSE_KEYWORDS.items():
            found = [kw for kw in keywords if kw in text_lower]
            if found:
                score = min(len(found) * 0.25, 1.0)
                detections.append({
                    'abuse_type': abuse_type,
                    'score': round(score, 2),
                    'keywords': found,
                    'urgency': 'URGENT' if score >= 0.75 else ('HIGH' if score >= 0.50 else 'MEDIUM'),
                })

        return sorted(detections, key=lambda x: x['score'], reverse=True)

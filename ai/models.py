from django.db import models


class ChatConversation(models.Model):
    """Conversation avec le chatbot juridique"""

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='chat_conversations',
        verbose_name='Utilisateur'
    )

    session_id = models.CharField(max_length=100, unique=True, verbose_name='ID de session')

    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de début')
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de fin')

    is_active = models.BooleanField(default=True, verbose_name='Active')

    # Contexte initial
    initial_topic = models.CharField(max_length=255, blank=True, verbose_name='Sujet initial')

    class Meta:
        verbose_name = 'Conversation chatbot'
        verbose_name_plural = 'Conversations chatbot'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.started_at.strftime('%d/%m/%Y %H:%M')}"


class ChatMessage(models.Model):
    """Message dans une conversation"""

    ROLE_CHOICES = (
        ('USER', 'Utilisateur'),
        ('ASSISTANT', 'Assistant IA'),
        ('SYSTEM', 'Système'),
    )

    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Conversation'
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name='Rôle')
    content = models.TextField(verbose_name='Contenu')

    # Métadonnées IA
    tokens_used = models.IntegerField(default=0, verbose_name='Tokens utilisés')
    model_used = models.CharField(max_length=50, blank=True, verbose_name='Modèle IA utilisé')
    confidence_score = models.FloatField(null=True, blank=True, verbose_name='Score de confiance')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')

    class Meta:
        verbose_name = 'Message chatbot'
        verbose_name_plural = 'Messages chatbot'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_role_display()} - {self.content[:50]}"


class DocumentAnalysis(models.Model):
    """Analyse OCR et IA d'un document"""

    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En traitement'),
        ('COMPLETED', 'Terminé'),
        ('FAILED', 'Échoué'),
    )

    DOCUMENT_TYPE_CHOICES = (
        ('CONTRACT', 'Contrat de travail'),
        ('PAYSLIP', 'Bulletin de paie'),
        ('TERMINATION', 'Lettre de licenciement'),
        ('COMPLAINT', 'Plainte écrite'),
        ('ID_CARD', 'Carte d\'identité'),
        ('OTHER', 'Autre'),
    )

    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='document_analyses',
        verbose_name='Uploadé par'
    )

    document_file = models.FileField(upload_to='ai/documents/', verbose_name='Document')
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        default='OTHER',
        verbose_name='Type de document'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='Statut')

    # Résultats OCR
    extracted_text = models.TextField(blank=True, verbose_name='Texte extrait (OCR)')
    ocr_confidence = models.FloatField(null=True, blank=True, verbose_name='Confiance OCR')

    # Analyse IA
    ai_summary = models.TextField(blank=True, verbose_name='Résumé IA')
    detected_issues = models.JSONField(default=list, blank=True, verbose_name='Problèmes détectés')
    key_clauses = models.JSONField(default=list, blank=True, verbose_name='Clauses clés')
    recommendations = models.TextField(blank=True, verbose_name='Recommandations')

    # Métadonnées
    language_detected = models.CharField(max_length=10, blank=True, verbose_name='Langue détectée')
    processing_time_seconds = models.FloatField(null=True, blank=True, verbose_name='Temps de traitement')

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Analyse de document'
        verbose_name_plural = 'Analyses de documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.get_status_display()}"


class ComplaintSimilarity(models.Model):
    """Similarité entre plaintes (clustering ML)"""

    complaint1 = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='similarities_as_source',
        verbose_name='Plainte 1'
    )

    complaint2 = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='similarities_as_target',
        verbose_name='Plainte 2'
    )

    similarity_score = models.FloatField(verbose_name='Score de similarité (0-1)')

    # Facteurs de similarité
    type_match = models.BooleanField(default=False, verbose_name='Type identique')
    employer_match = models.BooleanField(default=False, verbose_name='Employeur identique')
    text_similarity = models.FloatField(default=0, verbose_name='Similarité textuelle')

    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Similarité de plaintes'
        verbose_name_plural = 'Similarités de plaintes'
        unique_together = ['complaint1', 'complaint2']
        ordering = ['-similarity_score']

    def __str__(self):
        return f"{self.complaint1.complaint_number} ↔ {self.complaint2.complaint_number} ({self.similarity_score:.2f})"


class RiskPrediction(models.Model):
    """Prédiction de risques sociaux"""

    RISK_LEVEL_CHOICES = (
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyen'),
        ('HIGH', 'Élevé'),
        ('CRITICAL', 'Critique'),
    )

    RISK_TYPE_CHOICES = (
        ('STRIKE', 'Grève'),
        ('MASS_LAYOFF', 'Licenciement collectif'),
        ('SOCIAL_UNREST', 'Conflit social'),
        ('ACCIDENT_RISK', 'Risque d\'accident'),
        ('LABOR_DISPUTE', 'Litige du travail'),
    )

    enterprise = models.ForeignKey(
        'enterprises.Enterprise',
        on_delete=models.CASCADE,
        related_name='risk_predictions',
        verbose_name='Entreprise'
    )

    risk_type = models.CharField(max_length=20, choices=RISK_TYPE_CHOICES, verbose_name='Type de risque')
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, verbose_name='Niveau de risque')

    probability = models.FloatField(verbose_name='Probabilité (0-1)')

    # Facteurs de risque
    contributing_factors = models.JSONField(default=list, verbose_name='Facteurs contributifs')

    # Recommandations
    preventive_actions = models.TextField(blank=True, verbose_name='Actions préventives')

    # Métadonnées ML
    model_version = models.CharField(max_length=20, blank=True, verbose_name='Version du modèle')
    confidence_score = models.FloatField(null=True, blank=True, verbose_name='Confiance')

    predicted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name='Actif')

    class Meta:
        verbose_name = 'Prédiction de risque'
        verbose_name_plural = 'Prédictions de risques'
        ordering = ['-predicted_at']
        indexes = [
            models.Index(fields=['enterprise', 'risk_level']),
        ]

    def __str__(self):
        return f"{self.enterprise.name} - {self.get_risk_type_display()} ({self.get_risk_level_display()})"


class AbuseDetection(models.Model):
    """Détection automatique d'abus dans les plaintes"""

    ABUSE_TYPE_CHOICES = (
        ('HARASSMENT', 'Harcèlement'),
        ('DISCRIMINATION', 'Discrimination'),
        ('CHILD_LABOR', 'Travail des enfants'),
        ('FORCED_LABOR', 'Travail forcé'),
        ('UNSAFE_CONDITIONS', 'Conditions dangereuses'),
        ('WAGE_THEFT', 'Vol de salaire'),
    )

    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='abuse_detections',
        verbose_name='Plainte'
    )

    abuse_type = models.CharField(max_length=20, choices=ABUSE_TYPE_CHOICES, verbose_name='Type d\'abus')
    detection_score = models.FloatField(verbose_name='Score de détection (0-1)')

    # Preuves détectées
    evidence_keywords = models.JSONField(default=list, verbose_name='Mots-clés détectés')
    evidence_patterns = models.JSONField(default=list, verbose_name='Patterns détectés')

    # Actions recommandées
    urgency_level = models.CharField(
        max_length=20,
        choices=[('LOW', 'Faible'), ('MEDIUM', 'Moyen'), ('HIGH', 'Élevé'), ('URGENT', 'Urgent')],
        default='MEDIUM',
        verbose_name='Niveau d\'urgence'
    )
    recommended_actions = models.TextField(verbose_name='Actions recommandées')

    # Notification envoyée
    authorities_notified = models.BooleanField(default=False, verbose_name='Autorités notifiées')
    notified_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de notification')

    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Détection d\'abus'
        verbose_name_plural = 'Détections d\'abus'
        ordering = ['-detection_score', '-detected_at']

    def __str__(self):
        return f"{self.complaint.complaint_number} - {self.get_abuse_type_display()} ({self.detection_score:.2f})"

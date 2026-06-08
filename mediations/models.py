from django.db import models
from django.utils import timezone


class Mediation(models.Model):
    """Séance de médiation"""

    SESSION_TYPE_CHOICES = (
        ('PRESENTIAL', 'Présentiel'),
        ('ONLINE', 'En ligne (visioconférence)'),
        ('HYBRID', 'Hybride'),
    )

    STATUS_CHOICES = (
        ('SCHEDULED', 'Programmée'),
        ('ONGOING', 'En cours'),
        ('COMPLETED', 'Terminée'),
        ('CANCELLED', 'Annulée'),
        ('POSTPONED', 'Reportée'),
    )

    OUTCOME_CHOICES = (
        ('AGREEMENT', 'Accord trouvé'),
        ('PARTIAL_AGREEMENT', 'Accord partiel'),
        ('NO_AGREEMENT', 'Aucun accord'),
        ('PENDING', 'En attente'),
    )

    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='mediations',
        verbose_name='Plainte'
    )

    mediator = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='mediations_conducted',
        verbose_name='Médiateur'
    )

    session_date = models.DateTimeField(verbose_name='Date de la séance')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, verbose_name='Type de séance')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED', verbose_name='Statut')

    # Lieu (si présentiel ou hybride)
    location = models.TextField(blank=True, verbose_name='Lieu')

    # Lien visio (si en ligne ou hybride)
    meeting_link = models.URLField(blank=True, verbose_name='Lien de réunion')

    # Résultat
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default='PENDING', verbose_name='Résultat')
    outcome_notes = models.TextField(blank=True, verbose_name='Notes sur le résultat')

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de fin')

    class Meta:
        verbose_name = 'Médiation'
        verbose_name_plural = 'Médiations'
        ordering = ['-session_date']
        indexes = [
            models.Index(fields=['session_date', 'status']),
            models.Index(fields=['mediator', 'status']),
        ]

    def __str__(self):
        return f"Médiation {self.complaint.complaint_number} - {self.session_date.strftime('%d/%m/%Y')}"


class MediationParticipant(models.Model):
    """Participant à une médiation"""

    ROLE_CHOICES = (
        ('EMPLOYEE', 'Employé'),
        ('EMPLOYER', 'Employeur'),
        ('WITNESS', 'Témoin'),
        ('LAWYER', 'Avocat'),
        ('REPRESENTATIVE', 'Représentant'),
    )

    mediation = models.ForeignKey(
        Mediation,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name='Médiation'
    )

    participant = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Participant'
    )

    # Si le participant n'a pas de compte
    name = models.CharField(max_length=200, blank=True, verbose_name='Nom')
    email = models.EmailField(blank=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='Rôle')

    # Participation
    attended = models.BooleanField(default=False, verbose_name='A participé')
    signed = models.BooleanField(default=False, verbose_name='A signé')
    signature = models.ImageField(upload_to='mediations/signatures/', null=True, blank=True, verbose_name='Signature')

    # Convocation
    convoked_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de convocation')
    convocation_sent = models.BooleanField(default=False, verbose_name='Convocation envoyée')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Participant médiation'
        verbose_name_plural = 'Participants médiation'
        unique_together = ['mediation', 'participant']

    def __str__(self):
        name = self.participant.get_full_name() if self.participant else self.name
        return f"{name} - {self.get_role_display()}"


class MediationMinutes(models.Model):
    """Procès-verbal de médiation"""

    mediation = models.OneToOneField(
        Mediation,
        on_delete=models.CASCADE,
        related_name='minutes',
        verbose_name='Médiation'
    )

    # Contenu du PV
    opening_statement = models.TextField(verbose_name='Déclaration d\'ouverture')
    employee_statement = models.TextField(blank=True, verbose_name='Déclaration employé')
    employer_statement = models.TextField(blank=True, verbose_name='Déclaration employeur')
    discussion_summary = models.TextField(verbose_name='Résumé des discussions')
    agreements_reached = models.JSONField(default=list, verbose_name='Accords conclus')

    # Signatures
    signed_by_all = models.BooleanField(default=False, verbose_name='Signé par tous')
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de signature')

    # Document PDF
    pdf_file = models.FileField(upload_to='mediations/minutes/', null=True, blank=True, verbose_name='PV (PDF)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Procès-verbal'
        verbose_name_plural = 'Procès-verbaux'

    def __str__(self):
        return f"PV - {self.mediation.complaint.complaint_number}"


class Agreement(models.Model):
    """Accord de médiation signé"""

    STATUS_CHOICES = (
        ('DRAFT', 'Brouillon'),
        ('PENDING_SIGNATURE', 'En attente de signature'),
        ('SIGNED', 'Signé'),
        ('EXECUTED', 'Exécuté'),
        ('BREACHED', 'Violé'),
    )

    mediation = models.OneToOneField(
        Mediation,
        on_delete=models.CASCADE,
        related_name='agreement',
        verbose_name='Médiation'
    )

    # Contenu de l'accord
    agreement_text = models.TextField(verbose_name='Texte de l\'accord')
    terms = models.JSONField(default=list, verbose_name='Termes de l\'accord')

    # Obligations
    employee_obligations = models.TextField(blank=True, verbose_name='Obligations de l\'employé')
    employer_obligations = models.TextField(blank=True, verbose_name='Obligations de l\'employeur')

    # Compensation
    compensation_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Montant de compensation'
    )

    # Délai d'exécution
    execution_deadline = models.DateField(null=True, blank=True, verbose_name='Date limite d\'exécution')

    # Signatures
    employee_signature = models.ImageField(
        upload_to='mediations/agreements/signatures/',
        null=True,
        blank=True,
        verbose_name='Signature employé'
    )
    employer_signature = models.ImageField(
        upload_to='mediations/agreements/signatures/',
        null=True,
        blank=True,
        verbose_name='Signature employeur'
    )
    mediator_signature = models.ImageField(
        upload_to='mediations/agreements/signatures/',
        null=True,
        blank=True,
        verbose_name='Signature médiateur'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name='Statut')
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de signature')

    # Document PDF
    pdf_file = models.FileField(upload_to='mediations/agreements/', null=True, blank=True, verbose_name='Accord (PDF)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Accord de médiation'
        verbose_name_plural = 'Accords de médiation'

    def __str__(self):
        return f"Accord - {self.mediation.complaint.complaint_number}"

    def is_fully_signed(self):
        """Vérifie si toutes les signatures sont présentes"""
        return bool(
            self.employee_signature and
            self.employer_signature and
            self.mediator_signature
        )


class MediationDocument(models.Model):
    """Documents liés à la médiation"""

    DOCUMENT_TYPE_CHOICES = (
        ('CONVOCATION', 'Convocation'),
        ('MINUTES', 'Procès-verbal'),
        ('AGREEMENT', 'Accord'),
        ('EVIDENCE', 'Pièce justificative'),
        ('CORRESPONDENCE', 'Correspondance'),
        ('OTHER', 'Autre'),
    )

    mediation = models.ForeignKey(
        Mediation,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Médiation'
    )

    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, verbose_name='Type de document')
    title = models.CharField(max_length=255, verbose_name='Titre')
    file = models.FileField(upload_to='mediations/documents/', verbose_name='Fichier')

    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Uploadé par'
    )

    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'upload')

    class Meta:
        verbose_name = 'Document de médiation'
        verbose_name_plural = 'Documents de médiation'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.title}"


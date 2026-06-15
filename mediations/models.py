import uuid
from django.db import models
from django.utils import timezone


class Mediation(models.Model):
    """Séance de médiation / conciliation"""

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

    location = models.TextField(blank=True, verbose_name='Lieu')
    meeting_link = models.URLField(blank=True, verbose_name='Lien de réunion')

    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default='PENDING', verbose_name='Résultat')
    outcome_notes = models.TextField(blank=True, verbose_name='Notes sur le résultat')

    # ── Non-comparution employeur ────────────────────────────────────────────
    employer_no_show = models.BooleanField(
        default=False,
        verbose_name='Non-comparution employeur'
    )
    no_show_reported_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date de constat de non-comparution'
    )
    no_show_reported_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='no_show_reports',
        verbose_name='Constaté par'
    )
    pv_carence_generated = models.BooleanField(
        default=False,
        verbose_name='PV de carence généré'
    )
    pv_carence_file = models.FileField(
        upload_to='mediations/pv_carence/',
        null=True, blank=True,
        verbose_name='PV de non-comparution (PDF)'
    )
    # Nombre de reports successifs
    postpone_count = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Nombre de reports'
    )

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
            models.Index(fields=['employer_no_show']),
        ]

    def __str__(self):
        return f"Médiation {self.complaint.complaint_number} - {self.session_date.strftime('%d/%m/%Y')}"


class MediationParticipant(models.Model):
    """Participant à une séance de médiation"""

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
        null=True, blank=True,
        verbose_name='Compte utilisateur'
    )

    # Participant sans compte
    name = models.CharField(max_length=200, blank=True, verbose_name='Nom')
    email = models.EmailField(blank=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='Rôle')

    # Présence et signature
    attended = models.BooleanField(default=False, verbose_name='A participé')
    signed = models.BooleanField(default=False, verbose_name='A signé')
    signature = models.ImageField(
        upload_to='mediations/signatures/',
        null=True, blank=True,
        verbose_name='Signature'
    )

    # ── Convocation traçable ─────────────────────────────────────────────────
    convoked_at = models.DateTimeField(null=True, blank=True, verbose_name='Première convocation')
    last_attempt_at = models.DateTimeField(null=True, blank=True, verbose_name='Dernière tentative')
    convocation_attempts = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Nombre de tentatives de convocation'
    )
    convocation_sent = models.BooleanField(default=False, verbose_name='Convocation envoyée')

    # Token unique pour l'accusé de réception en ligne
    acknowledgment_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name='Token accusé de réception'
    )
    acknowledged_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Accusé de réception le'
    )
    # Canal par lequel l'accusé a été reçu : EMAIL / SMS / PORTAL / MANUAL
    acknowledgment_channel = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Canal de confirmation'
    )
    # L'agent peut forcer un accusé manuel (remise en main propre, téléphone…)
    manually_acknowledged = models.BooleanField(
        default=False,
        verbose_name='Accusé manuel (agent)'
    )
    manually_acknowledged_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='manual_acknowledgments',
        verbose_name='Acté par (agent)'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Participant médiation'
        verbose_name_plural = 'Participants médiation'
        unique_together = ['mediation', 'participant']

    def __str__(self):
        name = self.participant.get_full_name() if self.participant else self.name
        return f"{name} - {self.get_role_display()}"

    @property
    def is_acknowledged(self):
        return self.acknowledged_at is not None or self.manually_acknowledged

    @property
    def display_name(self):
        return self.participant.get_full_name() if self.participant else self.name


class ConvocationAttempt(models.Model):
    """Historique de chaque tentative de convocation — canal, statut, horodatage"""

    CHANNEL_CHOICES = (
        ('EMAIL', 'E-mail'),
        ('SMS',   'SMS'),
        ('PUSH',  'Notification push'),
        ('MANUAL','Remise manuelle'),
    )

    STATUS_CHOICES = (
        ('SENT',      'Envoyé'),
        ('DELIVERED', 'Distribué'),
        ('FAILED',    'Échec'),
        ('BOUNCED',   'Rejeté'),
    )

    participant = models.ForeignKey(
        MediationParticipant,
        on_delete=models.CASCADE,
        related_name='convocation_attempts_log',
        verbose_name='Participant'
    )
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, verbose_name='Canal')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SENT', verbose_name='Statut')
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='Envoyé le')
    # Identifiant renvoyé par le provider (SMS gateway ID, Sendgrid message ID…)
    provider_message_id = models.CharField(max_length=255, blank=True)
    error_detail = models.TextField(blank=True, verbose_name='Détail erreur')

    class Meta:
        verbose_name = 'Tentative de convocation'
        verbose_name_plural = 'Tentatives de convocation'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.participant.display_name} — {self.channel} — {self.sent_at.strftime('%d/%m/%Y %H:%M')}"


class MediationMinutes(models.Model):
    """Procès-verbal de médiation"""

    mediation = models.OneToOneField(
        Mediation,
        on_delete=models.CASCADE,
        related_name='minutes',
        verbose_name='Médiation'
    )

    opening_statement = models.TextField(verbose_name='Déclaration d\'ouverture')
    employee_statement = models.TextField(blank=True, verbose_name='Déclaration employé')
    employer_statement = models.TextField(blank=True, verbose_name='Déclaration employeur')
    discussion_summary = models.TextField(verbose_name='Résumé des discussions')
    agreements_reached = models.JSONField(default=list, verbose_name='Accords conclus')

    signed_by_all = models.BooleanField(default=False, verbose_name='Signé par tous')
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de signature')
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

    agreement_text = models.TextField(verbose_name='Texte de l\'accord')
    terms = models.JSONField(default=list, verbose_name='Termes de l\'accord')

    employee_obligations = models.TextField(blank=True, verbose_name='Obligations de l\'employé')
    employer_obligations = models.TextField(blank=True, verbose_name='Obligations de l\'employeur')

    compensation_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        verbose_name='Montant de compensation (FCFA)'
    )
    execution_deadline = models.DateField(null=True, blank=True, verbose_name='Date limite d\'exécution')

    employee_signature = models.ImageField(
        upload_to='mediations/agreements/signatures/',
        null=True, blank=True,
        verbose_name='Signature employé'
    )
    employer_signature = models.ImageField(
        upload_to='mediations/agreements/signatures/',
        null=True, blank=True,
        verbose_name='Signature employeur'
    )
    mediator_signature = models.ImageField(
        upload_to='mediations/agreements/signatures/',
        null=True, blank=True,
        verbose_name='Signature médiateur'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name='Statut')
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de signature')
    pdf_file = models.FileField(upload_to='mediations/agreements/', null=True, blank=True, verbose_name='Accord (PDF)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Accord de médiation'
        verbose_name_plural = 'Accords de médiation'

    def __str__(self):
        return f"Accord - {self.mediation.complaint.complaint_number}"

    def is_fully_signed(self):
        return bool(self.employee_signature and self.employer_signature and self.mediator_signature)


class MediationDocument(models.Model):
    """Documents liés à la médiation"""

    DOCUMENT_TYPE_CHOICES = (
        ('CONVOCATION', 'Convocation'),
        ('MINUTES', 'Procès-verbal'),
        ('AGREEMENT', 'Accord'),
        ('PV_CARENCE', 'PV de non-comparution'),
        ('EVIDENCE', 'Pièce justificative'),
        ('CORRESPONDENCE', 'Correspondance'),
        ('INFRACTION', 'PV d\'infraction'),
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

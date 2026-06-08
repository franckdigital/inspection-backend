from django.db import models
from django.utils import timezone
import random
import string


def generate_procedure_number():
    """Génère un numéro unique de procédure judiciaire"""
    year = timezone.now().year
    random_part = ''.join(random.choices(string.digits, k=6))
    return f"PROC-{year}-{random_part}"


class JudicialProcedure(models.Model):
    """Procédure judiciaire"""

    STATUS_CHOICES = (
        ('PREPARATION', 'En préparation'),
        ('SUBMITTED', 'Soumise au tribunal'),
        ('UNDER_REVIEW', 'En examen'),
        ('HEARING_SCHEDULED', 'Audience programmée'),
        ('AWAITING_DECISION', 'En délibéré'),
        ('DECIDED', 'Jugement rendu'),
        ('APPEAL', 'En appel'),
        ('CLOSED', 'Clôturée'),
    )

    PROCEDURE_TYPE_CHOICES = (
        ('LABOR_DISPUTE', 'Litige du travail'),
        ('WRONGFUL_TERMINATION', 'Licenciement abusif'),
        ('DISCRIMINATION', 'Discrimination'),
        ('HARASSMENT', 'Harcèlement'),
        ('UNPAID_WAGES', 'Salaires impayés'),
        ('WORKPLACE_ACCIDENT', 'Accident de travail'),
        ('OTHER', 'Autre'),
    )

    procedure_number = models.CharField(
        max_length=50,
        unique=True,
        default=generate_procedure_number,
        verbose_name='Numéro de procédure'
    )

    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='judicial_procedures',
        verbose_name='Plainte'
    )

    procedure_type = models.CharField(
        max_length=30,
        choices=PROCEDURE_TYPE_CHOICES,
        verbose_name='Type de procédure'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PREPARATION',
        verbose_name='Statut'
    )

    # Parties
    plaintiff = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='procedures_as_plaintiff',
        verbose_name='Plaignant'
    )

    defendant_name = models.CharField(max_length=255, verbose_name='Défendeur')
    defendant_representative = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Représentant du défendeur'
    )

    # Tribunal
    court_name = models.CharField(max_length=255, verbose_name='Tribunal')
    court_reference = models.CharField(max_length=100, blank=True, verbose_name='Référence tribunal')
    judge_name = models.CharField(max_length=255, blank=True, verbose_name='Juge')

    # Dates
    filed_date = models.DateField(null=True, blank=True, verbose_name='Date de dépôt')
    submission_date = models.DateField(null=True, blank=True, verbose_name='Date de transmission')

    # Responsable du dossier
    case_officer = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='judicial_procedures_managed',
        verbose_name='Chargé du dossier'
    )

    # Description
    summary = models.TextField(verbose_name='Résumé de l\'affaire')
    legal_grounds = models.TextField(blank=True, verbose_name='Fondements juridiques')
    claims = models.TextField(verbose_name='Demandes')

    # Montants
    claimed_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Montant réclamé'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Procédure judiciaire'
        verbose_name_plural = 'Procédures judiciaires'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['procedure_number']),
            models.Index(fields=['status', 'filed_date']),
        ]

    def __str__(self):
        return f"{self.procedure_number} - {self.complaint.complaint_number}"


class CourtDocument(models.Model):
    """Document judiciaire"""

    DOCUMENT_TYPE_CHOICES = (
        ('COMPLAINT_FORM', 'Formulaire de plainte'),
        ('EVIDENCE', 'Pièce à conviction'),
        ('WITNESS_STATEMENT', 'Témoignage'),
        ('EXPERT_REPORT', 'Rapport d\'expert'),
        ('LEGAL_BRIEF', 'Mémoire'),
        ('COURT_ORDER', 'Ordonnance'),
        ('SUMMONS', 'Assignation'),
        ('JUDGMENT', 'Jugement'),
        ('OTHER', 'Autre'),
    )

    procedure = models.ForeignKey(
        JudicialProcedure,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Procédure'
    )

    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name='Type de document'
    )

    title = models.CharField(max_length=255, verbose_name='Titre')
    description = models.TextField(blank=True, verbose_name='Description')

    file = models.FileField(upload_to='judicial/documents/', verbose_name='Fichier')

    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Uploadé par'
    )

    upload_date = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'upload')

    class Meta:
        verbose_name = 'Document judiciaire'
        verbose_name_plural = 'Documents judiciaires'
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.title}"


class Hearing(models.Model):
    """Audience judiciaire"""

    HEARING_TYPE_CHOICES = (
        ('PRELIMINARY', 'Audience préliminaire'),
        ('MAIN', 'Audience principale'),
        ('WITNESS', 'Audition de témoin'),
        ('EXPERT', 'Expertise'),
        ('DELIBERATION', 'Délibéré'),
        ('JUDGMENT', 'Prononcé du jugement'),
    )

    STATUS_CHOICES = (
        ('SCHEDULED', 'Programmée'),
        ('POSTPONED', 'Reportée'),
        ('COMPLETED', 'Tenue'),
        ('CANCELLED', 'Annulée'),
    )

    procedure = models.ForeignKey(
        JudicialProcedure,
        on_delete=models.CASCADE,
        related_name='hearings',
        verbose_name='Procédure'
    )

    hearing_type = models.CharField(
        max_length=20,
        choices=HEARING_TYPE_CHOICES,
        verbose_name='Type d\'audience'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED',
        verbose_name='Statut'
    )

    scheduled_date = models.DateTimeField(verbose_name='Date programmée')
    actual_date = models.DateTimeField(null=True, blank=True, verbose_name='Date effective')

    location = models.CharField(max_length=255, verbose_name='Lieu')
    room = models.CharField(max_length=100, blank=True, verbose_name='Salle')

    # Participants
    judge = models.CharField(max_length=255, blank=True, verbose_name='Juge')
    plaintiff_present = models.BooleanField(default=False, verbose_name='Plaignant présent')
    defendant_present = models.BooleanField(default=False, verbose_name='Défendeur présent')

    # Compte-rendu
    minutes = models.TextField(blank=True, verbose_name='Compte-rendu')
    next_steps = models.TextField(blank=True, verbose_name='Suites à donner')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Audience'
        verbose_name_plural = 'Audiences'
        ordering = ['-scheduled_date']

    def __str__(self):
        return f"{self.get_hearing_type_display()} - {self.scheduled_date.strftime('%d/%m/%Y')}"


class JudicialDecision(models.Model):
    """Décision de justice"""

    DECISION_TYPE_CHOICES = (
        ('JUDGMENT', 'Jugement'),
        ('ORDER', 'Ordonnance'),
        ('RULING', 'Arrêt'),
        ('SETTLEMENT', 'Transaction homologuée'),
    )

    OUTCOME_CHOICES = (
        ('FAVOR_PLAINTIFF', 'En faveur du plaignant'),
        ('FAVOR_DEFENDANT', 'En faveur du défendeur'),
        ('PARTIAL', 'Partiellement favorable'),
        ('DISMISSED', 'Rejetée'),
        ('SETTLED', 'Transaction'),
    )

    procedure = models.OneToOneField(
        JudicialProcedure,
        on_delete=models.CASCADE,
        related_name='decision',
        verbose_name='Procédure'
    )

    decision_type = models.CharField(
        max_length=20,
        choices=DECISION_TYPE_CHOICES,
        verbose_name='Type de décision'
    )

    outcome = models.CharField(
        max_length=20,
        choices=OUTCOME_CHOICES,
        verbose_name='Issue'
    )

    decision_date = models.DateField(verbose_name='Date de la décision')
    notification_date = models.DateField(null=True, blank=True, verbose_name='Date de notification')

    # Contenu
    summary = models.TextField(verbose_name='Résumé de la décision')
    full_text = models.TextField(blank=True, verbose_name='Texte intégral')

    # Montants
    awarded_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Montant accordé'
    )

    damages = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Dommages et intérêts'
    )

    legal_costs = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Frais de justice'
    )

    # Exécution
    is_enforceable = models.BooleanField(default=True, verbose_name='Exécutoire')
    is_final = models.BooleanField(default=False, verbose_name='Définitif')
    appeal_deadline = models.DateField(null=True, blank=True, verbose_name='Délai d\'appel')

    # Document
    decision_file = models.FileField(
        upload_to='judicial/decisions/',
        null=True,
        blank=True,
        verbose_name='Fichier de la décision'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Décision judiciaire'
        verbose_name_plural = 'Décisions judiciaires'
        ordering = ['-decision_date']

    def __str__(self):
        return f"{self.get_decision_type_display()} - {self.decision_date}"

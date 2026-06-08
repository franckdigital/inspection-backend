from django.db import models
from django.utils import timezone
from decimal import Decimal


class DomesticWorker(models.Model):
    """Employé de maison"""

    SPECIALIZATION_CHOICES = (
        ('HOUSEKEEPER', 'Femme/Homme de ménage'),
        ('COOK', 'Cuisinier(ère)'),
        ('NANNY', 'Nounou/Garde d\'enfants'),
        ('DRIVER', 'Chauffeur'),
        ('GARDENER', 'Jardinier'),
        ('SECURITY', 'Gardien/Sécurité'),
        ('CARETAKER', 'Aide à la personne'),
        ('GENERAL', 'Employé(e) polyvalent(e)'),
    )

    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='domestic_worker_profile',
        verbose_name='Utilisateur'
    )

    specialization = models.CharField(
        max_length=20,
        choices=SPECIALIZATION_CHOICES,
        verbose_name='Spécialisation'
    )

    years_experience = models.IntegerField(default=0, verbose_name='Années d\'expérience')

    # Certifications et formations
    certifications = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Certifications',
        help_text='Liste des certifications (premiers secours, cuisine, etc.)'
    )

    # Disponibilité
    is_available = models.BooleanField(default=True, verbose_name='Disponible')
    available_from = models.DateField(null=True, blank=True, verbose_name='Disponible à partir du')

    # Documents
    id_card = models.FileField(upload_to='domestic/id_cards/', null=True, blank=True, verbose_name='Carte d\'identité')
    cv = models.FileField(upload_to='domestic/cvs/', null=True, blank=True, verbose_name='CV')
    references = models.TextField(blank=True, verbose_name='Références')

    # Préférences
    preferred_work_days = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Jours de travail préférés',
        help_text='["lundi", "mardi", etc.]'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employé de maison'
        verbose_name_plural = 'Employés de maison'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_specialization_display()}"


class DomesticEmployer(models.Model):
    """Employeur particulier"""

    TYPE_CHOICES = (
        ('INDIVIDUAL', 'Particulier'),
        ('FAMILY', 'Famille'),
        ('COMPANY', 'Entreprise'),
    )

    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='domestic_employer_profile',
        verbose_name='Utilisateur'
    )

    employer_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='INDIVIDUAL', verbose_name='Type')

    household_size = models.IntegerField(default=1, verbose_name='Taille du foyer')
    has_children = models.BooleanField(default=False, verbose_name='A des enfants')
    has_pets = models.BooleanField(default=False, verbose_name='A des animaux')

    # Adresse principale
    address = models.TextField(verbose_name='Adresse')
    city = models.CharField(max_length=100, verbose_name='Ville')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employeur particulier'
        verbose_name_plural = 'Employeurs particuliers'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_employer_type_display()}"


class DomesticContract(models.Model):
    """Contrat de travail employé de maison"""

    STATUS_CHOICES = (
        ('DRAFT', 'Brouillon'),
        ('PENDING_SIGNATURE', 'En attente de signature'),
        ('ACTIVE', 'Actif'),
        ('SUSPENDED', 'Suspendu'),
        ('TERMINATED', 'Terminé'),
    )

    worker = models.ForeignKey(
        DomesticWorker,
        on_delete=models.CASCADE,
        related_name='contracts',
        verbose_name='Employé'
    )

    employer = models.ForeignKey(
        DomesticEmployer,
        on_delete=models.CASCADE,
        related_name='contracts',
        verbose_name='Employeur'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name='Statut')

    # Dates du contrat
    start_date = models.DateField(verbose_name='Date de début')
    end_date = models.DateField(null=True, blank=True, verbose_name='Date de fin')

    # Rémunération
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salaire mensuel')
    currency = models.CharField(max_length=3, default='CDF', verbose_name='Devise')
    payment_frequency = models.CharField(
        max_length=20,
        choices=[('MONTHLY', 'Mensuel'), ('WEEKLY', 'Hebdomadaire'), ('DAILY', 'Journalier')],
        default='MONTHLY',
        verbose_name='Fréquence de paiement'
    )

    # Horaires
    work_hours_start = models.TimeField(verbose_name='Heure de début')
    work_hours_end = models.TimeField(verbose_name='Heure de fin')
    weekly_hours = models.IntegerField(default=40, verbose_name='Heures hebdomadaires')

    # Jours de travail
    work_days = models.JSONField(
        default=list,
        verbose_name='Jours de travail',
        help_text='["lundi", "mardi", "mercredi", "jeudi", "vendredi"]'
    )

    days_off = models.JSONField(
        default=list,
        verbose_name='Jours de repos',
        help_text='["dimanche"]'
    )

    # Tâches
    tasks = models.JSONField(
        default=list,
        verbose_name='Tâches assignées',
        help_text='["ménage", "cuisine", "lessive", etc.]'
    )

    # Avantages
    accommodation_provided = models.BooleanField(default=False, verbose_name='Logement fourni')
    meals_provided = models.BooleanField(default=False, verbose_name='Repas fournis')
    transportation_allowance = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Allocation transport'
    )

    # Congés
    annual_leave_days = models.IntegerField(default=15, verbose_name='Jours de congé annuels')

    # Signatures
    worker_signature = models.ImageField(
        upload_to='domestic/signatures/',
        null=True,
        blank=True,
        verbose_name='Signature employé'
    )
    employer_signature = models.ImageField(
        upload_to='domestic/signatures/',
        null=True,
        blank=True,
        verbose_name='Signature employeur'
    )
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de signature')

    # Document PDF
    contract_pdf = models.FileField(
        upload_to='domestic/contracts/',
        null=True,
        blank=True,
        verbose_name='Contrat PDF'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contrat employé de maison'
        verbose_name_plural = 'Contrats employés de maison'
        ordering = ['-created_at']

    def __str__(self):
        return f"Contrat {self.worker.user.get_full_name()} - {self.employer.user.get_full_name()}"

    def is_fully_signed(self):
        """Vérifie si le contrat est complètement signé"""
        return bool(self.worker_signature and self.employer_signature)


class TimeTracking(models.Model):
    """Pointage GPS employé de maison"""

    contract = models.ForeignKey(
        DomesticContract,
        on_delete=models.CASCADE,
        related_name='time_trackings',
        verbose_name='Contrat'
    )

    date = models.DateField(verbose_name='Date')

    # Pointage arrivée
    check_in_time = models.DateTimeField(verbose_name='Heure d\'arrivée')
    check_in_latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Latitude arrivée')
    check_in_longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Longitude arrivée')
    check_in_address = models.CharField(max_length=255, blank=True, verbose_name='Adresse arrivée')

    # Pointage départ
    check_out_time = models.DateTimeField(null=True, blank=True, verbose_name='Heure de départ')
    check_out_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Latitude départ'
    )
    check_out_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Longitude départ'
    )
    check_out_address = models.CharField(max_length=255, blank=True, verbose_name='Adresse départ')

    # Calculs
    hours_worked = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Heures travaillées'
    )
    overtime_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Heures supplémentaires'
    )

    # Notes
    notes = models.TextField(blank=True, verbose_name='Notes')
    is_validated = models.BooleanField(default=False, verbose_name='Validé')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pointage'
        verbose_name_plural = 'Pointages'
        ordering = ['-date', '-check_in_time']
        unique_together = ['contract', 'date']

    def __str__(self):
        return f"{self.contract.worker.user.get_full_name()} - {self.date}"

    def calculate_hours(self):
        """Calcule les heures travaillées et supplémentaires"""
        if self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            total_hours = Decimal(delta.total_seconds() / 3600)
            self.hours_worked = total_hours

            # Calculer heures sup (> 8h par jour)
            daily_limit = Decimal('8.0')
            if total_hours > daily_limit:
                self.overtime_hours = total_hours - daily_limit
            else:
                self.overtime_hours = Decimal('0')

            self.save()


class OvertimeSession(models.Model):
    """Session d'heures supplémentaires déclarée manuellement (plusieurs par jour)"""

    tracking = models.ForeignKey(
        TimeTracking,
        on_delete=models.CASCADE,
        related_name='overtime_sessions',
        verbose_name='Pointage du jour'
    )
    start_time = models.DateTimeField(verbose_name='Début heures sup')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='Fin heures sup')
    duration_minutes = models.IntegerField(default=0, verbose_name='Durée (minutes)')
    reason = models.CharField(max_length=255, blank=True, verbose_name='Motif')
    is_active = models.BooleanField(default=True, verbose_name='En cours')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Session heures supplémentaires'
        verbose_name_plural = 'Sessions heures supplémentaires'
        ordering = ['-start_time']

    def __str__(self):
        return f"HS {self.tracking.date} — {self.tracking.contract.worker.user.get_full_name()}"

    def stop(self):
        from django.utils import timezone
        if not self.end_time:
            self.end_time = timezone.now()
            delta = self.end_time - self.start_time
            self.duration_minutes = max(0, int(delta.total_seconds() / 60))
            self.is_active = False
            self.save()
            # Mettre à jour overtime_hours du TimeTracking parent
            total_ot_hours = sum(
                s.duration_minutes for s in self.tracking.overtime_sessions.filter(end_time__isnull=False)
            ) / 60
            self.tracking.overtime_hours = Decimal(str(total_ot_hours))
            self.tracking.save(update_fields=['overtime_hours'])


class MonthlyPayslip(models.Model):
    """Bulletin de paie mensuel"""

    STATUS_CHOICES = (
        ('DRAFT', 'Brouillon'),
        ('GENERATED', 'Généré'),
        ('PAID', 'Payé'),
    )

    contract = models.ForeignKey(
        DomesticContract,
        on_delete=models.CASCADE,
        related_name='payslips',
        verbose_name='Contrat'
    )

    month = models.DateField(verbose_name='Mois')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name='Statut')

    # Heures
    regular_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name='Heures normales')
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name='Heures supplémentaires')

    # Salaires
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salaire de base')
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Paie heures sup')
    transportation_allowance = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Allocation transport'
    )
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Primes')

    # Déductions
    absences_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Retenues absences')
    social_security = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='CNPS')
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Impôts')
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Autres retenues')

    # Totaux
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salaire brut')
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total retenues')
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salaire net')

    # Paiement
    payment_date = models.DateField(null=True, blank=True, verbose_name='Date de paiement')
    payment_method = models.CharField(
        max_length=20,
        choices=[('CASH', 'Espèces'), ('BANK_TRANSFER', 'Virement'), ('MOBILE_MONEY', 'Mobile Money')],
        blank=True,
        verbose_name='Méthode de paiement'
    )

    # Document
    pdf_file = models.FileField(upload_to='domestic/payslips/', null=True, blank=True, verbose_name='Bulletin PDF')

    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de génération')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bulletin de paie'
        verbose_name_plural = 'Bulletins de paie'
        ordering = ['-month']
        unique_together = ['contract', 'month']

    def __str__(self):
        return f"Bulletin {self.contract.worker.user.get_full_name()} - {self.month.strftime('%B %Y')}"

    def calculate_totals(self):
        """Calcule les totaux"""
        # Brut
        self.gross_pay = (
            self.base_salary +
            self.overtime_pay +
            self.transportation_allowance +
            self.bonuses
        )

        # Déductions
        self.total_deductions = (
            self.absences_deduction +
            self.social_security +
            self.taxes +
            self.other_deductions
        )

        # Net
        self.net_pay = self.gross_pay - self.total_deductions
        self.save()


class LeaveRequest(models.Model):
    """Demande de congé"""

    LEAVE_TYPE_CHOICES = (
        ('ANNUAL', 'Congé annuel'),
        ('SICK', 'Congé maladie'),
        ('MATERNITY', 'Congé maternité'),
        ('UNPAID', 'Congé sans solde'),
        ('EMERGENCY', 'Congé exceptionnel'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvé'),
        ('REJECTED', 'Rejeté'),
    )

    contract = models.ForeignKey(
        DomesticContract,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        verbose_name='Contrat'
    )

    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES, verbose_name='Type de congé')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='Statut')

    start_date = models.DateField(verbose_name='Date de début')
    end_date = models.DateField(verbose_name='Date de fin')
    days_count = models.IntegerField(verbose_name='Nombre de jours')

    reason = models.TextField(verbose_name='Raison')
    supporting_document = models.FileField(
        upload_to='domestic/leave_documents/',
        null=True,
        blank=True,
        verbose_name='Document justificatif'
    )

    # Réponse
    response_comment = models.TextField(blank=True, verbose_name='Commentaire de réponse')
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de réponse')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Demande de congé'
        verbose_name_plural = 'Demandes de congé'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_leave_type_display()} - {self.contract.worker.user.get_full_name()}"


def generate_voice_case_number():
    from django.utils import timezone
    import random, string
    year = timezone.now().year
    num = ''.join(random.choices(string.digits, k=6))
    return f"DOM-{year}-{num}"


class VoiceComplaint(models.Model):
    LANGUAGE_CHOICES = (
        ('DIOULA', 'Dioula'),
        ('BAOULE', 'Baoulé'),
        ('BETE', 'Bété'),
        ('SENOUFO', 'Sénoufo'),
        ('ANYIN', 'Anyin'),
        ('FRENCH', 'Français'),
        ('OTHER', 'Autre'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('ASSIGNED', 'Assigné'),
        ('IN_PROGRESS', 'En cours'),
        ('RESPONDED', 'Répondu'),
        ('ASSISTANCE_REQUESTED', 'Assistance linguistique demandée'),
        ('CLOSED', 'Clôturé'),
    )

    case_number = models.CharField(
        max_length=30, unique=True, default=generate_voice_case_number,
        verbose_name='Numéro de dossier'
    )
    worker = models.ForeignKey(
        DomesticWorker, on_delete=models.CASCADE,
        related_name='voice_complaints', verbose_name='Employée'
    )
    audio_file = models.FileField(
        upload_to='voice_complaints/audio/', verbose_name='Message vocal'
    )
    duration_seconds = models.IntegerField(default=0, verbose_name='Durée (s)')
    detected_language = models.CharField(
        max_length=20, choices=LANGUAGE_CHOICES, blank=True, verbose_name='Langue détectée'
    )
    language_confidence = models.FloatField(default=0.0, verbose_name='Confiance (%)')
    commune = models.CharField(max_length=100, blank=True, verbose_name='Commune')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default='PENDING', verbose_name='Statut'
    )
    assigned_inspector = models.ForeignKey(
        'users.User', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='assigned_voice_complaints', verbose_name='Inspecteur assigné'
    )
    inspector_response_text = models.TextField(blank=True, verbose_name='Réponse texte')
    inspector_response_audio = models.FileField(
        upload_to='voice_complaints/responses/', null=True, blank=True,
        verbose_name='Réponse audio'
    )
    language_assistance_requested = models.BooleanField(
        default=False, verbose_name='Assistance linguistique demandée'
    )

    # Langue choisie par l'utilisateur avant l'enregistrement
    selected_language = models.CharField(
        max_length=20, choices=LANGUAGE_CHOICES, blank=True,
        verbose_name='Langue choisie'
    )

    # Transcription & traduction (remplies par Whisper + GPT en arrière-plan)
    TRANSCRIPTION_STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En cours'),
        ('DONE', 'Terminée'),
        ('FAILED', 'Échouée'),
    )
    transcription_status = models.CharField(
        max_length=20, choices=TRANSCRIPTION_STATUS_CHOICES,
        default='PENDING', verbose_name='Statut transcription'
    )
    transcription_original = models.TextField(
        blank=True, verbose_name='Transcription (langue originale)'
    )
    transcription_french = models.TextField(
        blank=True, verbose_name='Traduction en français'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Déclaration vocale'
        verbose_name_plural = 'Déclarations vocales'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.case_number} - {self.worker.user.get_full_name()}"

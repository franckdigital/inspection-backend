from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django_countries.fields import CountryField


class Enterprise(models.Model):
    SECTOR_CHOICES = (
        ('AGRICULTURE', 'Agriculture'),
        ('INDUSTRIE', 'Industrie'),
        ('COMMERCE', 'Commerce'),
        ('SERVICES', 'Services'),
        ('CONSTRUCTION', 'Construction'),
        ('TRANSPORT', 'Transport'),
        ('SANTE', 'Santé'),
        ('EDUCATION', 'Éducation'),
        ('FINANCE', 'Finance'),
        ('TECHNOLOGIE', 'Technologie'),
        ('HOTELLERIE', 'Hôtellerie et Restauration'),
        ('AUTRE', 'Autre'),
    )

    LEGAL_FORM_CHOICES = (
        ('SARL', 'SARL'),
        ('SA', 'SA'),
        ('SAS', 'SAS'),
        ('EI', 'Entreprise Individuelle'),
        ('SASU', 'SASU'),
        ('SNC', 'SNC'),
        ('AUTRE', 'Autre'),
    )

    name = models.CharField(max_length=255, verbose_name='Nom de l\'entreprise')
    legal_form = models.CharField(max_length=50, choices=LEGAL_FORM_CHOICES, verbose_name='Forme juridique')

    rccm = models.CharField(max_length=100, unique=True, verbose_name='RCCM')
    cc = models.CharField(max_length=100, blank=True, verbose_name='CC (Registre de Commerce)')
    nif = models.CharField(max_length=100, unique=True, verbose_name='NIF')
    cnps_number = models.CharField(max_length=100, blank=True, verbose_name='Numéro CNPS')

    sector = models.CharField(max_length=50, choices=SECTOR_CHOICES, verbose_name='Secteur d\'activité')
    description = models.TextField(blank=True, verbose_name='Description')

    headquarters_address = models.TextField(verbose_name='Adresse du siège')
    city = models.CharField(max_length=100, verbose_name='Ville')
    region = models.CharField(max_length=100, blank=True, verbose_name='Région/Département')
    country = CountryField(default='CG', verbose_name='Pays')

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Latitude')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Longitude')

    phone_number = PhoneNumberField(verbose_name='Téléphone')
    email = models.EmailField(verbose_name='Email')
    website = models.URLField(blank=True, verbose_name='Site web')

    employee_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Nombre d\'employés'
    )

    founding_date = models.DateField(null=True, blank=True, verbose_name='Date de création')

    inspection_zone = models.ForeignKey(
        'inspections.InspectionZone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enterprises',
        verbose_name='Zone d\'inspection'
    )

    compliance_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Score de conformité'
    )

    risk_level = models.CharField(
        max_length=20,
        choices=(
            ('LOW', 'Faible'),
            ('MEDIUM', 'Moyen'),
            ('HIGH', 'Élevé'),
            ('CRITICAL', 'Critique'),
        ),
        default='LOW',
        verbose_name='Niveau de risque social'
    )

    is_active = models.BooleanField(default=True, verbose_name='Active')
    is_verified = models.BooleanField(default=False, verbose_name='Vérifiée')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Entreprise'
        verbose_name_plural = 'Entreprises'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rccm']),
            models.Index(fields=['nif']),
            models.Index(fields=['sector']),
            models.Index(fields=['city']),
            models.Index(fields=['compliance_score']),
            models.Index(fields=['risk_level']),
        ]

    def __str__(self):
        return f"{self.name} ({self.rccm})"

    def update_compliance_score(self):
        total_inspections = self.inspection_records.count()
        if total_inspections == 0:
            self.compliance_score = 50
        else:
            compliant_inspections = self.inspection_records.filter(result='COMPLIANT').count()
            self.compliance_score = int((compliant_inspections / total_inspections) * 100)

        if self.compliance_score >= 80:
            self.risk_level = 'LOW'
        elif self.compliance_score >= 60:
            self.risk_level = 'MEDIUM'
        elif self.compliance_score >= 40:
            self.risk_level = 'HIGH'
        else:
            self.risk_level = 'CRITICAL'

        self.save(update_fields=['compliance_score', 'risk_level'])


class EnterpriseBranch(models.Model):
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='branches', verbose_name='Entreprise')

    name = models.CharField(max_length=255, verbose_name='Nom de la succursale')
    address = models.TextField(verbose_name='Adresse')
    city = models.CharField(max_length=100, verbose_name='Ville')

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Latitude')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Longitude')

    phone_number = PhoneNumberField(verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')

    manager_name = models.CharField(max_length=200, blank=True, verbose_name='Nom du responsable')
    employee_count = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Nombre d\'employés')

    is_active = models.BooleanField(default=True, verbose_name='Active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Succursale'
        verbose_name_plural = 'Succursales'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.enterprise.name}"


class EnterpriseDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ('RCCM', 'RCCM'),
        ('NIF', 'NIF'),
        ('CNPS', 'Attestation CNPS'),
        ('STATUTS', 'Statuts'),
        ('LICENCE', 'Licence d\'exploitation'),
        ('AUTRE', 'Autre'),
    )

    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='documents', verbose_name='Entreprise')

    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, verbose_name='Type de document')
    title = models.CharField(max_length=255, verbose_name='Titre')
    file = models.FileField(upload_to='enterprises/documents/', verbose_name='Fichier')

    issue_date = models.DateField(null=True, blank=True, verbose_name='Date d\'émission')
    expiry_date = models.DateField(null=True, blank=True, verbose_name='Date d\'expiration')

    is_verified = models.BooleanField(default=False, verbose_name='Vérifié')

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Document d\'entreprise'
        verbose_name_plural = 'Documents d\'entreprise'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.document_type} - {self.enterprise.name}"


class EnterpriseHistory(models.Model):
    EVENT_TYPE_CHOICES = (
        ('CREATION', 'Création'),
        ('UPDATE', 'Mise à jour'),
        ('INSPECTION', 'Inspection'),
        ('COMPLAINT', 'Plainte'),
        ('SANCTION', 'Sanction'),
        ('PROCEDURE', 'Procédure judiciaire'),
    )

    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='history', verbose_name='Entreprise')

    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, verbose_name='Type d\'événement')
    description = models.TextField(verbose_name='Description')

    performed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Effectué par'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historique d\'entreprise'
        verbose_name_plural = 'Historiques d\'entreprise'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.enterprise.name} - {self.created_at}"

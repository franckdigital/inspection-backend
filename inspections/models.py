from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField


class InspectionZone(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nom de la zone')
    code = models.CharField(max_length=50, unique=True, verbose_name='Code')
    description = models.TextField(blank=True, verbose_name='Description')

    region = models.CharField(max_length=100, verbose_name='Région')
    city = models.CharField(max_length=100, blank=True, verbose_name='Ville')

    address = models.TextField(blank=True, verbose_name='Adresse')
    phone_number = PhoneNumberField(blank=True, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Latitude')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Longitude')

    head_inspector = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_zones',
        verbose_name='Chef d\'inspection'
    )

    is_active = models.BooleanField(default=True, verbose_name='Active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Zone d\'inspection'
        verbose_name_plural = 'Zones d\'inspection'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class InspectionRecord(models.Model):
    INSPECTION_TYPE_CHOICES = (
        ('ROUTINE', 'Routine'),
        ('FOLLOW_UP', 'Suivi'),
        ('COMPLAINT', 'Suite à plainte'),
        ('SPOT_CHECK', 'Contrôle inopiné'),
    )

    RESULT_CHOICES = (
        ('COMPLIANT', 'Conforme'),
        ('MINOR_ISSUES', 'Non-conformités mineures'),
        ('MAJOR_ISSUES', 'Non-conformités majeures'),
        ('NON_COMPLIANT', 'Non conforme'),
    )

    enterprise = models.ForeignKey(
        'enterprises.Enterprise',
        on_delete=models.CASCADE,
        related_name='inspection_records',
        verbose_name='Entreprise'
    )

    inspector = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='conducted_inspections',
        verbose_name='Inspecteur'
    )

    inspection_type = models.CharField(max_length=50, choices=INSPECTION_TYPE_CHOICES, verbose_name='Type d\'inspection')

    scheduled_date = models.DateTimeField(verbose_name='Date prévue')
    actual_date = models.DateTimeField(null=True, blank=True, verbose_name='Date effective')

    location = models.TextField(verbose_name='Lieu')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    findings = models.TextField(verbose_name='Constats')
    recommendations = models.TextField(blank=True, verbose_name='Recommandations')

    result = models.CharField(max_length=50, choices=RESULT_CHOICES, verbose_name='Résultat')

    photos = models.JSONField(default=list, blank=True, verbose_name='Photos')

    report_file = models.FileField(upload_to='inspections/reports/', null=True, blank=True, verbose_name='Rapport')

    is_completed = models.BooleanField(default=False, verbose_name='Terminée')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Enregistrement d\'inspection'
        verbose_name_plural = 'Enregistrements d\'inspection'
        ordering = ['-scheduled_date']

    def __str__(self):
        return f"Inspection de {self.enterprise.name} - {self.scheduled_date.strftime('%d/%m/%Y')}"

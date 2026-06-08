from django.db import models
from django.utils import timezone
import random
import string


def generate_complaint_number():
    year = timezone.now().year
    random_part = ''.join(random.choices(string.digits, k=6))
    return f"PLT-{year}-{random_part}"


class Complaint(models.Model):
    COMPLAINT_TYPE_CHOICES = (
        ('UNPAID_SALARY', 'Salaire impayé'),
        ('TERMINATION', 'Licenciement abusif'),
        ('HARASSMENT', 'Harcèlement'),
        ('ACCIDENT', 'Accident de travail'),
        ('OVERTIME', 'Heures supplémentaires non payées'),
        ('LEAVE', 'Congés non respectés'),
        ('CONTRACT', 'Problème de contrat'),
        ('DISCRIMINATION', 'Discrimination'),
        ('WORKING_CONDITIONS', 'Conditions de travail'),
        ('OTHER', 'Autre'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('ASSIGNED', 'Assignée'),
        ('IN_PROGRESS', 'En cours de traitement'),
        ('UNDER_INVESTIGATION', 'En enquête'),
        ('MEDIATION', 'En médiation'),
        ('RESOLVED', 'Résolue'),
        ('CLOSED', 'Clôturée'),
        ('ESCALATED', 'Escaladée'),
        ('JUDICIAL', 'Procédure judiciaire'),
    )

    PRIORITY_CHOICES = (
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyenne'),
        ('HIGH', 'Haute'),
        ('URGENT', 'Urgente'),
    )

    complaint_number = models.CharField(max_length=50, unique=True, default=generate_complaint_number, verbose_name='Numéro de plainte')

    complainant = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='filed_complaints',
        verbose_name='Plaignant'
    )

    complaint_type = models.CharField(max_length=50, choices=COMPLAINT_TYPE_CHOICES, verbose_name='Type de plainte')
    subject = models.CharField(max_length=255, verbose_name='Objet')
    description = models.TextField(verbose_name='Description détaillée')

    enterprise = models.ForeignKey(
        'enterprises.Enterprise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints',
        verbose_name='Entreprise concernée'
    )

    employer_name = models.CharField(max_length=255, blank=True, verbose_name='Nom de l\'employeur')
    workplace_address = models.TextField(verbose_name='Adresse du lieu de travail')
    workplace_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    workplace_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    incident_date = models.DateField(null=True, blank=True, verbose_name='Date de l\'incident')

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING', verbose_name='Statut')
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='MEDIUM', verbose_name='Priorité')

    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        verbose_name='Assigné à'
    )

    inspection_zone = models.ForeignKey(
        'inspections.InspectionZone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints',
        verbose_name='Zone d\'inspection'
    )

    resolution = models.TextField(blank=True, verbose_name='Résolution')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de clôture')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Date de modification')

    class Meta:
        verbose_name = 'Plainte'
        verbose_name_plural = 'Plaintes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['complaint_number']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.complaint_number} - {self.get_complaint_type_display()}"

    def assign_to_zone(self):
        if self.workplace_latitude and self.workplace_longitude:
            from inspections.models import InspectionZone
            zones = InspectionZone.objects.filter(is_active=True)
            for zone in zones:
                if zone.latitude and zone.longitude:
                    distance = ((self.workplace_latitude - zone.latitude) ** 2 +
                              (self.workplace_longitude - zone.longitude) ** 2) ** 0.5
                    if distance < 0.5:
                        self.inspection_zone = zone
                        self.save(update_fields=['inspection_zone'])
                        break


class ComplaintDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ('CONTRACT', 'Contrat de travail'),
        ('PAYSLIP', 'Bulletin de paie'),
        ('PHOTO', 'Photo'),
        ('AUDIO', 'Audio'),
        ('VIDEO', 'Vidéo'),
        ('LETTER', 'Lettre/Courrier'),
        ('OTHER', 'Autre'),
    )

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='documents', verbose_name='Plainte')

    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, verbose_name='Type de document')
    title = models.CharField(max_length=255, verbose_name='Titre')
    file = models.FileField(upload_to='complaints/documents/', verbose_name='Fichier')

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Document de plainte'
        verbose_name_plural = 'Documents de plainte'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.document_type} - {self.complaint.complaint_number}"


class ComplaintComment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments', verbose_name='Plainte')

    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name='Auteur'
    )

    comment = models.TextField(verbose_name='Commentaire')

    is_internal = models.BooleanField(default=False, verbose_name='Interne (non visible au plaignant)')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
        ordering = ['created_at']

    def __str__(self):
        return f"Commentaire par {self.author.get_full_name()} - {self.created_at}"


class ComplaintStatusHistory(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='status_history', verbose_name='Plainte')

    from_status = models.CharField(max_length=50, blank=True, verbose_name='Ancien statut')
    to_status = models.CharField(max_length=50, verbose_name='Nouveau statut')

    changed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Modifié par'
    )

    reason = models.TextField(blank=True, verbose_name='Raison du changement')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historique de statut'
        verbose_name_plural = 'Historiques de statut'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.from_status} → {self.to_status} - {self.created_at}"


class ComplaintNotification(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='notifications', verbose_name='Plainte')

    recipient = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name='Destinataire'
    )

    message = models.TextField(verbose_name='Message')

    is_read = models.BooleanField(default=False, verbose_name='Lu')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Lu à')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification pour {self.recipient.get_full_name()} - {self.created_at}"

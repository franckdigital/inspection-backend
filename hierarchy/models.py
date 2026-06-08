from django.db import models
from django.utils import timezone


class WorkflowApproval(models.Model):
    """Approbation hiérarchique des dossiers"""

    LEVEL_CHOICES = (
        ('INSPECTOR', 'Inspecteur'),
        ('CHIEF', 'Chef d\'Inspection'),
        ('REGIONAL', 'Directeur Régional'),
        ('NATIONAL', 'Directeur Général'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvé'),
        ('REJECTED', 'Rejeté'),
    )

    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name='Plainte'
    )

    approver = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='approvals_given',
        verbose_name='Approbateur'
    )

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, verbose_name='Niveau hiérarchique')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='Statut')

    comment = models.TextField(blank=True, verbose_name='Commentaire')

    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Date d\'approbation')

    class Meta:
        verbose_name = 'Approbation'
        verbose_name_plural = 'Approbations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['complaint', 'status']),
            models.Index(fields=['approver', 'status']),
        ]

    def __str__(self):
        return f"{self.get_level_display()} - {self.complaint.complaint_number} - {self.get_status_display()}"


class Escalation(models.Model):
    """Escalade de dossier"""

    REASON_CHOICES = (
        ('DELAY', 'Délai dépassé'),
        ('COMPLEXITY', 'Complexité du dossier'),
        ('CONFLICT', 'Conflit d\'intérêt'),
        ('MANUAL', 'Escalade manuelle'),
        ('OTHER', 'Autre'),
    )

    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='escalations',
        verbose_name='Plainte'
    )

    from_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='escalations_sent',
        verbose_name='De'
    )

    to_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='escalations_received',
        verbose_name='Vers'
    )

    reason = models.CharField(max_length=20, choices=REASON_CHOICES, verbose_name='Raison')
    description = models.TextField(verbose_name='Description')

    escalated_at = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'escalade')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de résolution')
    is_resolved = models.BooleanField(default=False, verbose_name='Résolu')

    class Meta:
        verbose_name = 'Escalade'
        verbose_name_plural = 'Escalades'
        ordering = ['-escalated_at']

    def __str__(self):
        return f"Escalade {self.complaint.complaint_number} : {self.from_user.get_full_name()} → {self.to_user.get_full_name()}"


class Delegation(models.Model):
    """Délégation de pouvoir"""

    from_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='delegations_given',
        verbose_name='Délégant'
    )

    to_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='delegations_received',
        verbose_name='Délégataire'
    )

    start_date = models.DateField(verbose_name='Date de début')
    end_date = models.DateField(verbose_name='Date de fin')

    reason = models.TextField(verbose_name='Raison de la délégation')
    permissions = models.JSONField(
        default=list,
        verbose_name='Permissions déléguées',
        help_text='Liste des permissions (approve, reject, reassign, etc.)'
    )

    is_active = models.BooleanField(default=True, verbose_name='Active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Délégation'
        verbose_name_plural = 'Délégations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user.get_full_name()} → {self.to_user.get_full_name()} ({self.start_date} - {self.end_date})"

    def is_valid(self):
        """Vérifie si la délégation est valide aujourd'hui"""
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date


class ReassignmentHistory(models.Model):
    """Historique des réaffectations"""

    complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.CASCADE,
        related_name='reassignments',
        verbose_name='Plainte'
    )

    from_inspector = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reassignments_from',
        verbose_name='Ancien inspecteur'
    )

    to_inspector = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reassignments_to',
        verbose_name='Nouvel inspecteur'
    )

    reassigned_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reassignments_done',
        verbose_name='Réaffecté par'
    )

    reason = models.TextField(verbose_name='Raison de la réaffectation')

    reassigned_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de réaffectation')

    class Meta:
        verbose_name = 'Réaffectation'
        verbose_name_plural = 'Réaffectations'
        ordering = ['-reassigned_at']

    def __str__(self):
        return f"{self.complaint.complaint_number} : {self.from_inspector.get_full_name()} → {self.to_inspector.get_full_name()}"

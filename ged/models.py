from django.db import models
import os


class DocumentCategory(models.Model):
    """Catégorie de documents"""

    name = models.CharField(max_length=255, unique=True, verbose_name='Nom')
    code = models.CharField(max_length=50, unique=True, verbose_name='Code')
    description = models.TextField(blank=True, verbose_name='Description')

    # Règles de rétention
    retention_years = models.IntegerField(default=5, verbose_name='Durée de rétention (années)')
    is_archivable = models.BooleanField(default=True, verbose_name='Archivable')

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name='Catégorie parent'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Catégorie de document'
        verbose_name_plural = 'Catégories de documents'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Document(models.Model):
    """Document numérique dans la GED"""

    STATUS_CHOICES = (
        ('DRAFT', 'Brouillon'),
        ('ACTIVE', 'Actif'),
        ('ARCHIVED', 'Archivé'),
        ('DELETED', 'Supprimé'),
    )

    title = models.CharField(max_length=255, verbose_name='Titre')
    reference_number = models.CharField(max_length=100, unique=True, verbose_name='Numéro de référence')

    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name='documents',
        verbose_name='Catégorie'
    )

    file = models.FileField(upload_to='ged/documents/%Y/%m/', verbose_name='Fichier')
    file_size = models.BigIntegerField(default=0, verbose_name='Taille (octets)')
    file_type = models.CharField(max_length=50, blank=True, verbose_name='Type de fichier')

    description = models.TextField(blank=True, verbose_name='Description')

    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Métadonnées')
    tags = models.JSONField(default=list, blank=True, verbose_name='Tags')

    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name='Statut')

    # Sécurité
    is_confidential = models.BooleanField(default=False, verbose_name='Confidentiel')
    access_level = models.IntegerField(default=1, verbose_name='Niveau d\'accès (1-5)')

    # Ownership
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='created_documents',
        verbose_name='Créé par'
    )

    # Archivage
    archived_at = models.DateTimeField(null=True, blank=True, verbose_name='Archivé le')
    archive_location = models.CharField(max_length=255, blank=True, verbose_name='Emplacement archive')

    # Relations
    related_complaint = models.ForeignKey(
        'complaints.Complaint',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ged_documents',
        verbose_name='Plainte liée'
    )

    related_enterprise = models.ForeignKey(
        'enterprises.Enterprise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ged_documents',
        verbose_name='Entreprise liée'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference_number']),
            models.Index(fields=['status', 'category']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.reference_number} - {self.title}"

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.file_type = os.path.splitext(self.file.name)[1]
        super().save(*args, **kwargs)


class DocumentVersion(models.Model):
    """Historique des versions d'un document"""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='Document'
    )

    version_number = models.IntegerField(verbose_name='Numéro de version')
    file = models.FileField(upload_to='ged/versions/%Y/%m/', verbose_name='Fichier')

    change_description = models.TextField(blank=True, verbose_name='Description des changements')

    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        verbose_name='Créé par'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Version de document'
        verbose_name_plural = 'Versions de documents'
        ordering = ['-version_number']
        unique_together = ['document', 'version_number']

    def __str__(self):
        return f"{self.document.reference_number} - v{self.version_number}"


class DocumentAccess(models.Model):
    """Log des accès aux documents"""

    ACTION_CHOICES = (
        ('VIEW', 'Consultation'),
        ('DOWNLOAD', 'Téléchargement'),
        ('EDIT', 'Modification'),
        ('SHARE', 'Partage'),
        ('DELETE', 'Suppression'),
    )

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='access_logs',
        verbose_name='Document'
    )

    user = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        verbose_name='Utilisateur'
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Action')

    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Adresse IP')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Accès document'
        verbose_name_plural = 'Accès documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', 'created_at']),
            models.Index(fields=['user', 'action']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_action_display()} - {self.document.reference_number}"


class Archive(models.Model):
    """Archive physique ou numérique"""

    ARCHIVE_TYPE_CHOICES = (
        ('PHYSICAL', 'Physique'),
        ('DIGITAL', 'Numérique'),
        ('CLOUD', 'Cloud'),
    )

    name = models.CharField(max_length=255, verbose_name='Nom de l\'archive')
    archive_type = models.CharField(max_length=20, choices=ARCHIVE_TYPE_CHOICES, verbose_name='Type')

    location = models.CharField(max_length=500, verbose_name='Emplacement')
    capacity_gb = models.FloatField(null=True, blank=True, verbose_name='Capacité (GB)')
    used_space_gb = models.FloatField(default=0, verbose_name='Espace utilisé (GB)')

    is_active = models.BooleanField(default=True, verbose_name='Active')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Archive'
        verbose_name_plural = 'Archives'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_archive_type_display()})"

from django.db import models


class SystemConfiguration(models.Model):
    """Configuration système"""

    CONFIG_TYPE_CHOICES = (
        ('GENERAL', 'Général'),
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PAYMENT', 'Paiement'),
        ('SECURITY', 'Sécurité'),
        ('CUSTOM', 'Personnalisé'),
    )

    key = models.CharField(max_length=255, unique=True, verbose_name='Clé')
    value = models.TextField(verbose_name='Valeur')
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPE_CHOICES, default='CUSTOM', verbose_name='Type')

    description = models.TextField(blank=True, verbose_name='Description')

    is_encrypted = models.BooleanField(default=False, verbose_name='Cryptée')
    is_active = models.BooleanField(default=True, verbose_name='Active')

    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Modifié par'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuration système'
        verbose_name_plural = 'Configurations système'
        ordering = ['key']

    def __str__(self):
        return f"{self.key} = {self.value[:50]}"


class AuditLog(models.Model):
    """Journal d'audit complet"""

    ACTION_CHOICES = (
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('VIEW', 'Consultation'),
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
    )

    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Utilisateur'
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Action')

    # Objet modifié
    model_name = models.CharField(max_length=100, verbose_name='Modèle')
    object_id = models.IntegerField(null=True, blank=True, verbose_name='ID objet')
    object_repr = models.CharField(max_length=255, blank=True, verbose_name='Représentation')

    # Changements
    changes = models.JSONField(default=dict, blank=True, verbose_name='Changements')

    # Contexte
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Adresse IP')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log d\'audit'
        verbose_name_plural = 'Logs d\'audit'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.model_name} ({self.created_at})"


class BackupLog(models.Model):
    """Historique des sauvegardes"""

    BACKUP_TYPE_CHOICES = (
        ('FULL', 'Complète'),
        ('INCREMENTAL', 'Incrémentale'),
        ('DATABASE', 'Base de données'),
        ('FILES', 'Fichiers'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('RUNNING', 'En cours'),
        ('COMPLETED', 'Terminée'),
        ('FAILED', 'Échouée'),
    )

    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPE_CHOICES, verbose_name='Type')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='Statut')

    file_path = models.CharField(max_length=500, blank=True, verbose_name='Chemin fichier')
    file_size_mb = models.FloatField(default=0, verbose_name='Taille (MB)')

    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Démarré à')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Terminé à')

    error_message = models.TextField(blank=True, verbose_name='Message d\'erreur')

    triggered_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Lancé par'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de sauvegarde'
        verbose_name_plural = 'Logs de sauvegarde'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_backup_type_display()} - {self.get_status_display()} ({self.created_at})"


class MaintenanceMode(models.Model):
    """Mode maintenance"""

    is_active = models.BooleanField(default=False, verbose_name='Actif')

    message = models.TextField(default='Système en maintenance. Retour imminent.', verbose_name='Message')

    scheduled_start = models.DateTimeField(null=True, blank=True, verbose_name='Début programmé')
    scheduled_end = models.DateTimeField(null=True, blank=True, verbose_name='Fin programmée')

    activated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='activated_maintenance',
        verbose_name='Activé par'
    )

    deactivated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deactivated_maintenance',
        verbose_name='Désactivé par'
    )

    activated_at = models.DateTimeField(null=True, blank=True, verbose_name='Activé à')
    deactivated_at = models.DateTimeField(null=True, blank=True, verbose_name='Désactivé à')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mode maintenance'
        verbose_name_plural = 'Modes maintenance'
        ordering = ['-created_at']

    def __str__(self):
        status = 'ACTIF' if self.is_active else 'INACTIF'
        return f"Maintenance {status}"


class Permission(models.Model):
    """Permission personnalisée"""

    code = models.CharField(max_length=100, unique=True, verbose_name='Code')
    name = models.CharField(max_length=255, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')

    module = models.CharField(max_length=100, blank=True, verbose_name='Module')

    is_active = models.BooleanField(default=True, verbose_name='Active')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['module', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Role(models.Model):
    """Rôle avec permissions"""

    name = models.CharField(max_length=255, unique=True, verbose_name='Nom')
    code = models.CharField(max_length=100, unique=True, verbose_name='Code')
    description = models.TextField(blank=True, verbose_name='Description')

    permissions = models.ManyToManyField(Permission, blank=True, verbose_name='Permissions')

    is_system = models.BooleanField(default=False, verbose_name='Rôle système')
    is_active = models.BooleanField(default=True, verbose_name='Actif')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.permissions.count()} permissions)"

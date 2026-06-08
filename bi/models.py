from django.db import models


class Dashboard(models.Model):
    """Dashboard personnalisé"""

    name = models.CharField(max_length=255, verbose_name='Nom')
    slug = models.SlugField(unique=True, verbose_name='Slug')

    description = models.TextField(blank=True, verbose_name='Description')

    # Configuration
    widgets = models.JSONField(default=list, verbose_name='Widgets')
    layout = models.JSONField(default=dict, verbose_name='Layout')

    # Visibilité
    is_public = models.BooleanField(default=False, verbose_name='Public')
    allowed_roles = models.JSONField(default=list, blank=True, verbose_name='Rôles autorisés')

    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='created_dashboards',
        verbose_name='Créé par'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'
        ordering = ['name']

    def __str__(self):
        return self.name


class Report(models.Model):
    """Rapport BI"""

    REPORT_TYPE_CHOICES = (
        ('TABLE', 'Tableau'),
        ('CHART', 'Graphique'),
        ('PIVOT', 'Tableau croisé'),
        ('CUSTOM', 'Personnalisé'),
    )

    STATUS_CHOICES = (
        ('DRAFT', 'Brouillon'),
        ('PUBLISHED', 'Publié'),
        ('ARCHIVED', 'Archivé'),
    )

    title = models.CharField(max_length=255, verbose_name='Titre')
    slug = models.SlugField(unique=True, verbose_name='Slug')

    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, verbose_name='Type')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name='Statut')

    description = models.TextField(blank=True, verbose_name='Description')

    # Requête SQL ou config
    query = models.TextField(blank=True, verbose_name='Requête SQL')
    query_params = models.JSONField(default=dict, blank=True, verbose_name='Paramètres requête')

    # Configuration visuelle
    chart_config = models.JSONField(default=dict, blank=True, verbose_name='Configuration graphique')

    # Planification
    is_scheduled = models.BooleanField(default=False, verbose_name='Planifié')
    schedule_cron = models.CharField(max_length=100, blank=True, verbose_name='Cron schedule')

    # Cache
    cached_data = models.JSONField(default=dict, blank=True, verbose_name='Données en cache')
    cache_expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Expiration cache')

    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='created_reports',
        verbose_name='Créé par'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rapport'
        verbose_name_plural = 'Rapports'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"


class KPI(models.Model):
    """Indicateur de performance clé"""

    name = models.CharField(max_length=255, verbose_name='Nom')
    code = models.CharField(max_length=100, unique=True, verbose_name='Code')

    description = models.TextField(blank=True, verbose_name='Description')

    # Calcul
    calculation_method = models.TextField(verbose_name='Méthode de calcul')
    unit = models.CharField(max_length=50, blank=True, verbose_name='Unité')

    # Seuils
    target_value = models.FloatField(null=True, blank=True, verbose_name='Valeur cible')
    warning_threshold = models.FloatField(null=True, blank=True, verbose_name='Seuil alerte')
    critical_threshold = models.FloatField(null=True, blank=True, verbose_name='Seuil critique')

    # Valeur actuelle
    current_value = models.FloatField(null=True, blank=True, verbose_name='Valeur actuelle')
    last_calculated_at = models.DateTimeField(null=True, blank=True, verbose_name='Dernier calcul')

    # Catégorie
    category = models.CharField(max_length=100, blank=True, verbose_name='Catégorie')

    is_active = models.BooleanField(default=True, verbose_name='Actif')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'KPI'
        verbose_name_plural = 'KPIs'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class DataExport(models.Model):
    """Export de données"""

    EXPORT_FORMAT_CHOICES = (
        ('CSV', 'CSV'),
        ('EXCEL', 'Excel'),
        ('PDF', 'PDF'),
        ('JSON', 'JSON'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En cours'),
        ('COMPLETED', 'Terminé'),
        ('FAILED', 'Échoué'),
    )

    title = models.CharField(max_length=255, verbose_name='Titre')

    export_format = models.CharField(max_length=20, choices=EXPORT_FORMAT_CHOICES, verbose_name='Format')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='Statut')

    # Configuration
    model_name = models.CharField(max_length=100, verbose_name='Modèle')
    filters = models.JSONField(default=dict, blank=True, verbose_name='Filtres')
    columns = models.JSONField(default=list, blank=True, verbose_name='Colonnes')

    # Fichier
    file = models.FileField(upload_to='exports/%Y/%m/', blank=True, verbose_name='Fichier')
    file_size_mb = models.FloatField(default=0, verbose_name='Taille (MB)')

    # Métadonnées
    rows_count = models.IntegerField(default=0, verbose_name='Nombre de lignes')

    requested_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='data_exports',
        verbose_name='Demandé par'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Terminé à')

    error_message = models.TextField(blank=True, verbose_name='Message d\'erreur')

    class Meta:
        verbose_name = 'Export de données'
        verbose_name_plural = 'Exports de données'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_export_format_display()} ({self.get_status_display()})"

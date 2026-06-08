from django.db import models


class DailyStatistics(models.Model):
    """Statistiques quotidiennes agrégées"""

    date = models.DateField(unique=True, verbose_name='Date')

    # Plaintes
    complaints_total = models.IntegerField(default=0, verbose_name='Total plaintes')
    complaints_new = models.IntegerField(default=0, verbose_name='Nouvelles plaintes')
    complaints_resolved = models.IntegerField(default=0, verbose_name='Plaintes résolues')
    complaints_pending = models.IntegerField(default=0, verbose_name='Plaintes en cours')

    # Inspections
    inspections_total = models.IntegerField(default=0, verbose_name='Total inspections')
    inspections_completed = models.IntegerField(default=0, verbose_name='Inspections terminées')

    # Entreprises
    enterprises_total = models.IntegerField(default=0, verbose_name='Total entreprises')
    enterprises_at_risk = models.IntegerField(default=0, verbose_name='Entreprises à risque')

    # Médiations
    mediations_scheduled = models.IntegerField(default=0, verbose_name='Médiations programmées')
    mediations_successful = models.IntegerField(default=0, verbose_name='Médiations réussies')

    # Taux calculés
    resolution_rate = models.FloatField(default=0, verbose_name='Taux de résolution (%)')
    average_resolution_days = models.FloatField(default=0, verbose_name='Délai moyen résolution (jours)')

    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Statistiques quotidiennes'
        verbose_name_plural = 'Statistiques quotidiennes'
        ordering = ['-date']

    def __str__(self):
        return f"Stats {self.date}"


class MonthlyReport(models.Model):
    """Rapport mensuel consolidé"""

    month = models.DateField(unique=True, verbose_name='Mois')

    # Totaux
    total_complaints = models.IntegerField(default=0)
    total_inspections = models.IntegerField(default=0)
    total_enterprises = models.IntegerField(default=0)

    # KPIs
    resolution_rate = models.FloatField(default=0)
    compliance_rate = models.FloatField(default=0)
    average_resolution_time = models.FloatField(default=0)

    # Par type
    complaints_by_type = models.JSONField(default=dict)
    complaints_by_region = models.JSONField(default=dict)

    # Top secteurs
    top_sectors_issues = models.JSONField(default=list)

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rapport mensuel'
        verbose_name_plural = 'Rapports mensuels'
        ordering = ['-month']

    def __str__(self):
        return f"Rapport {self.month.strftime('%B %Y')}"

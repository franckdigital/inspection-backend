from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('domestic', '0005_domesticcontract_inspector'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FieldVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zone_label', models.CharField(blank=True, max_length=200, verbose_name='Zone / Quartier')),
                ('commune', models.CharField(blank=True, max_length=100, verbose_name='Commune')),
                ('planned_date', models.DateTimeField(verbose_name='Date prévue')),
                ('actual_date', models.DateTimeField(blank=True, null=True, verbose_name='Date effective')),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('address', models.CharField(blank=True, max_length=500, verbose_name='Adresse de visite')),
                ('status', models.CharField(
                    choices=[
                        ('PLANNED', 'Planifiée'),
                        ('IN_PROGRESS', 'En cours'),
                        ('COMPLETED', 'Terminée'),
                        ('CANCELLED', 'Annulée'),
                    ],
                    default='PLANNED',
                    max_length=20,
                    verbose_name='Statut',
                )),
                ('worker_present', models.BooleanField(default=True, verbose_name='Employé présent')),
                ('employer_present', models.BooleanField(default=False, verbose_name='Employeur présent')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('findings', models.TextField(blank=True, verbose_name='Constats')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('inspector', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='field_visits',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Inspecteur',
                )),
                ('contract', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='field_visits',
                    to='domestic.domesticcontract',
                    verbose_name='Contrat lié',
                )),
            ],
            options={
                'verbose_name': 'Visite de terrain',
                'verbose_name_plural': 'Visites de terrain',
                'ordering': ['-planned_date'],
            },
        ),
    ]

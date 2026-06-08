from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inspections', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Commune',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('code', models.CharField(blank=True, max_length=20, unique=True, verbose_name='Code')),
                ('city', models.CharField(blank=True, max_length=100, verbose_name='Ville')),
                ('region', models.CharField(blank=True, max_length=100, verbose_name='Région')),
                ('is_active', models.BooleanField(default=True)),
                ('zone', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='communes',
                    to='inspections.inspectionzone',
                    verbose_name="Zone d'inspection",
                )),
            ],
            options={
                'verbose_name': 'Commune',
                'verbose_name_plural': 'Communes',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='InspectorZoneAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(
                    choices=[('HEAD', "Chef d'inspection"), ('MEMBER', 'Inspecteur membre')],
                    default='MEMBER', max_length=20,
                )),
                ('languages_spoken', models.JSONField(blank=True, default=list, verbose_name='Langues parlées')),
                ('is_active', models.BooleanField(default=True)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('inspector', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='zone_assignments',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('zone', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='inspector_assignments',
                    to='inspections.inspectionzone',
                )),
            ],
            options={
                'verbose_name': 'Affectation inspecteur-zone',
                'verbose_name_plural': 'Affectations inspecteur-zone',
                'ordering': ['-assigned_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='inspectorzoneassignment',
            unique_together={('zone', 'inspector')},
        ),
    ]

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def populate_acknowledgment_tokens(apps, schema_editor):
    """Assign a unique UUID to every existing MediationParticipant row."""
    MediationParticipant = apps.get_model('mediations', 'MediationParticipant')
    for participant in MediationParticipant.objects.filter(acknowledgment_token__isnull=True):
        participant.acknowledgment_token = uuid.uuid4()
        participant.save(update_fields=['acknowledgment_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('mediations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── 1. New fields on Mediation ──────────────────────────────────────
        migrations.AddField(
            model_name='mediation',
            name='employer_no_show',
            field=models.BooleanField(default=False, verbose_name='Non-comparution employeur'),
        ),
        migrations.AddField(
            model_name='mediation',
            name='no_show_reported_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date de constat de non-comparution'),
        ),
        migrations.AddField(
            model_name='mediation',
            name='no_show_reported_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='no_show_reports',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Constaté par',
            ),
        ),
        migrations.AddField(
            model_name='mediation',
            name='pv_carence_generated',
            field=models.BooleanField(default=False, verbose_name='PV de carence généré'),
        ),
        migrations.AddField(
            model_name='mediation',
            name='pv_carence_file',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='mediations/pv_carence/',
                verbose_name='PV de non-comparution (PDF)',
            ),
        ),
        migrations.AddField(
            model_name='mediation',
            name='postpone_count',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Nombre de reports'),
        ),
        migrations.AddIndex(
            model_name='mediation',
            index=models.Index(fields=['employer_no_show'], name='mediations__employe_no_show_idx'),
        ),

        # ── 2. New ConvocationAttempt model ────────────────────────────────
        migrations.CreateModel(
            name='ConvocationAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(
                    choices=[
                        ('EMAIL', 'E-mail'),
                        ('SMS', 'SMS'),
                        ('PUSH', 'Notification push'),
                        ('MANUAL', 'Remise manuelle'),
                    ],
                    max_length=10,
                    verbose_name='Canal',
                )),
                ('status', models.CharField(
                    choices=[
                        ('SENT', 'Envoyé'),
                        ('DELIVERED', 'Distribué'),
                        ('FAILED', 'Échec'),
                        ('BOUNCED', 'Rejeté'),
                    ],
                    default='SENT',
                    max_length=10,
                    verbose_name='Statut',
                )),
                ('sent_at', models.DateTimeField(auto_now_add=True, verbose_name='Envoyé le')),
                ('provider_message_id', models.CharField(blank=True, max_length=255)),
                ('error_detail', models.TextField(blank=True, verbose_name='Détail erreur')),
                ('participant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='convocation_attempts_log',
                    to='mediations.mediationparticipant',
                    verbose_name='Participant',
                )),
            ],
            options={
                'verbose_name': 'Tentative de convocation',
                'verbose_name_plural': 'Tentatives de convocation',
                'ordering': ['-sent_at'],
            },
        ),

        # ── 3. New fields on MediationParticipant (non-unique ones first) ──
        migrations.AddField(
            model_name='mediationparticipant',
            name='last_attempt_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Dernière tentative'),
        ),
        migrations.AddField(
            model_name='mediationparticipant',
            name='convocation_attempts',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Nombre de tentatives de convocation'),
        ),
        migrations.AddField(
            model_name='mediationparticipant',
            name='acknowledged_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Accusé de réception le'),
        ),
        migrations.AddField(
            model_name='mediationparticipant',
            name='acknowledgment_channel',
            field=models.CharField(blank=True, max_length=10, verbose_name='Canal de confirmation'),
        ),
        migrations.AddField(
            model_name='mediationparticipant',
            name='manually_acknowledged',
            field=models.BooleanField(default=False, verbose_name='Accusé manuel (agent)'),
        ),
        migrations.AddField(
            model_name='mediationparticipant',
            name='manually_acknowledged_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='manual_acknowledgments',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Acté par (agent)',
            ),
        ),

        # ── 4. Add acknowledgment_token as nullable (no unique yet) ────────
        migrations.AddField(
            model_name='mediationparticipant',
            name='acknowledgment_token',
            field=models.UUIDField(
                null=True,
                blank=True,
                verbose_name='Token accusé de réception',
            ),
        ),

        # ── 5. Populate a unique UUID for every existing row ────────────────
        migrations.RunPython(
            populate_acknowledgment_tokens,
            reverse_code=migrations.RunPython.noop,
        ),

        # ── 6. Now enforce NOT NULL + UNIQUE ───────────────────────────────
        migrations.AlterField(
            model_name='mediationparticipant',
            name='acknowledgment_token',
            field=models.UUIDField(
                default=uuid.uuid4,
                unique=True,
                verbose_name='Token accusé de réception',
            ),
        ),

        # ── 7. Update MediationDocument choices (adds PV_CARENCE/INFRACTION)
        migrations.AlterField(
            model_name='mediationdocument',
            name='document_type',
            field=models.CharField(
                choices=[
                    ('CONVOCATION', 'Convocation'),
                    ('MINUTES', 'Procès-verbal'),
                    ('AGREEMENT', 'Accord'),
                    ('PV_CARENCE', 'PV de non-comparution'),
                    ('EVIDENCE', 'Pièce justificative'),
                    ('CORRESPONDENCE', 'Correspondance'),
                    ('INFRACTION', "PV d'infraction"),
                    ('OTHER', 'Autre'),
                ],
                max_length=20,
                verbose_name='Type de document',
            ),
        ),

        # ── 8. Update convoked_at verbose_name ─────────────────────────────
        migrations.AlterField(
            model_name='mediationparticipant',
            name='convoked_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Première convocation'),
        ),
    ]

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('domestic', '0004_voicecomplaint_transcription_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='domesticcontract',
            name='inspector',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='supervised_contracts',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Inspecteur du travail',
            ),
        ),
    ]

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('domestic', '0006_fieldvisit'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='voicecomplaint',
            name='assistance_inspector',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='linguistic_assistance_cases',
                to=settings.AUTH_USER_MODEL,
                verbose_name="Inspecteur assistant",
            ),
        ),
        migrations.AddField(
            model_name='voicecomplaint',
            name='assistance_note',
            field=models.TextField(blank=True, verbose_name="Note d'interprétation"),
        ),
        migrations.AddField(
            model_name='voicecomplaint',
            name='assistance_responded_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date réponse assistance'),
        ),
    ]

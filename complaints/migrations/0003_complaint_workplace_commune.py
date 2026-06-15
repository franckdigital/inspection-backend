from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='complaint',
            name='workplace_commune',
            field=models.CharField(
                blank=True,
                help_text=(
                    'Commune ou sous-préfecture (ex: Yopougon, Cocody, Marcory). '
                    'Utilisée pour l\'assignation automatique.'
                ),
                max_length=100,
                verbose_name='Commune du lieu de travail',
            ),
        ),
    ]

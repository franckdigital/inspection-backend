from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_add_employe_maison_user_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeeprofile',
            name='assigned_inspector',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'user_type__in': ['INSPECTEUR', 'CHEF_INSPECTION']},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='supervised_employees',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Inspecteur assigné',
            ),
        ),
    ]

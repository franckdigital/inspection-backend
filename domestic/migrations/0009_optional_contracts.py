from django.db import migrations, models
import django.db.models.deletion


def populate_worker_from_contract(apps, schema_editor):
    """Backfill worker FK from contract on existing records."""
    TimeTracking = apps.get_model('domestic', 'TimeTracking')
    for tt in TimeTracking.objects.filter(worker__isnull=True, contract__isnull=False).select_related('contract__worker'):
        tt.worker_id = tt.contract.worker_id
        tt.save(update_fields=['worker'])

    MonthlyPayslip = apps.get_model('domestic', 'MonthlyPayslip')
    for ps in MonthlyPayslip.objects.filter(worker__isnull=True, contract__isnull=False).select_related('contract__worker'):
        ps.worker_id = ps.contract.worker_id
        ps.save(update_fields=['worker'])

    LeaveRequest = apps.get_model('domestic', 'LeaveRequest')
    for lr in LeaveRequest.objects.filter(worker__isnull=True, contract__isnull=False).select_related('contract__worker'):
        lr.worker_id = lr.contract.worker_id
        lr.save(update_fields=['worker'])

    FieldVisit = apps.get_model('domestic', 'FieldVisit')
    for fv in FieldVisit.objects.filter(worker__isnull=True, contract__isnull=False).select_related('contract__worker'):
        fv.worker_id = fv.contract.worker_id
        fv.save(update_fields=['worker'])


class Migration(migrations.Migration):

    dependencies = [
        ('domestic', '0008_domesticworker_assigned_inspector'),
    ]

    operations = [
        # ── TimeTracking ───────────────────────────────────────────────────────
        migrations.AddField(
            model_name='timetracking',
            name='worker',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='time_trackings_direct',
                to='domestic.domesticworker',
                verbose_name='Employé',
            ),
        ),
        migrations.AlterField(
            model_name='timetracking',
            name='contract',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='time_trackings',
                to='domestic.domesticcontract',
                verbose_name='Contrat',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='timetracking',
            unique_together=set(),
        ),

        # ── MonthlyPayslip ─────────────────────────────────────────────────────
        migrations.AddField(
            model_name='monthlypayslip',
            name='worker',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='payslips_direct',
                to='domestic.domesticworker',
                verbose_name='Employé',
            ),
        ),
        migrations.AlterField(
            model_name='monthlypayslip',
            name='contract',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payslips',
                to='domestic.domesticcontract',
                verbose_name='Contrat',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='monthlypayslip',
            unique_together=set(),
        ),

        # ── LeaveRequest ───────────────────────────────────────────────────────
        migrations.AddField(
            model_name='leaverequest',
            name='worker',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='leave_requests_direct',
                to='domestic.domesticworker',
                verbose_name='Employé',
            ),
        ),
        migrations.AlterField(
            model_name='leaverequest',
            name='contract',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='leave_requests',
                to='domestic.domesticcontract',
                verbose_name='Contrat',
            ),
        ),

        # ── FieldVisit ─────────────────────────────────────────────────────────
        migrations.AddField(
            model_name='fieldvisit',
            name='worker',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='field_visits_direct',
                to='domestic.domesticworker',
                verbose_name='Employé lié',
            ),
        ),

        # ── Data migration ─────────────────────────────────────────────────────
        migrations.RunPython(populate_worker_from_contract, migrations.RunPython.noop),
    ]

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('einspection')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # ── Plaintes ──────────────────────────────────────────────────────────────
    'escalate-overdue-complaints': {
        'task': 'complaints.tasks.escalate_overdue_complaints',
        'schedule': crontab(minute=0),          # toutes les heures
    },
    'send-complaint-reminders': {
        'task': 'complaints.tasks.send_complaint_reminders',
        'schedule': crontab(minute=0, hour=8),  # chaque matin à 08h00
    },

    # ── Médiation ─────────────────────────────────────────────────────────────
    'check-convocation-deadlines': {
        'task': 'mediations.tasks.check_convocation_deadlines',
        'schedule': crontab(minute=0, hour='*/2'),  # toutes les 2 heures
    },
    'auto-escalate-no-response': {
        'task': 'mediations.tasks.auto_escalate_no_response',
        'schedule': crontab(minute=30, hour=7),  # 07h30 chaque matin
    },

    # ── Procédures judiciaires ────────────────────────────────────────────────
    'send-hearing-reminders': {
        'task': 'judicial.tasks.send_hearing_reminders',
        'schedule': crontab(minute=0, hour='*/2'),
    },
    'alert-overdue-procedures': {
        'task': 'judicial.tasks.alert_overdue_procedures',
        'schedule': crontab(minute=0, hour=6),   # 06h00 chaque matin
    },

    # ── Emploi domestique ─────────────────────────────────────────────────────
    'generate-monthly-payslips': {
        'task': 'domestic.tasks.generate_monthly_payslips',
        'schedule': crontab(minute=0, hour=6, day_of_month=1),  # 1er du mois
    },
    'send-leave-approval-reminders': {
        'task': 'domestic.tasks.send_leave_approval_reminders',
        'schedule': crontab(minute=0, hour=9),
    },
    'expire-old-contracts': {
        'task': 'domestic.tasks.expire_old_contracts',
        'schedule': crontab(minute=0, hour=0),  # minuit
    },

    # ── Notifications ─────────────────────────────────────────────────────────
    'retry-failed-emails': {
        'task': 'notifications.tasks.retry_failed_emails',
        'schedule': crontab(minute='*/30'),     # toutes les 30 minutes
    },
    'retry-failed-sms': {
        'task': 'notifications.tasks.retry_failed_sms',
        'schedule': crontab(minute='*/30'),
    },
    'process-pending-notifications': {
        'task': 'notifications.tasks.process_pending_notifications',
        'schedule': crontab(minute='*/5'),      # toutes les 5 minutes
    },
}

app.conf.timezone = 'Africa/Abidjan'

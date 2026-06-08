from django.db import models


class EmailTemplate(models.Model):
    """Template d'email réutilisable"""

    TEMPLATE_TYPE_CHOICES = (
        ('COMPLAINT_CREATED', 'Plainte créée'),
        ('COMPLAINT_ASSIGNED', 'Plainte assignée'),
        ('STATUS_UPDATE', 'Mise à jour statut'),
        ('MEDIATION_INVITATION', 'Invitation médiation'),
        ('HEARING_NOTIFICATION', 'Notification audience'),
        ('DECISION_NOTIFICATION', 'Notification décision'),
        ('CONTRACT_SIGNED', 'Contrat signé'),
        ('PAYSLIP_GENERATED', 'Bulletin généré'),
        ('LEAVE_APPROVED', 'Congé approuvé'),
        ('CUSTOM', 'Personnalisé'),
    )

    name = models.CharField(max_length=255, unique=True, verbose_name='Nom du template')
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPE_CHOICES, verbose_name='Type')

    subject = models.CharField(max_length=255, verbose_name='Sujet')
    html_content = models.TextField(verbose_name='Contenu HTML')
    text_content = models.TextField(blank=True, verbose_name='Contenu texte')

    # Variables disponibles
    available_variables = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Variables disponibles',
        help_text='Ex: ["user_name", "complaint_number", "date"]'
    )

    is_active = models.BooleanField(default=True, verbose_name='Actif')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Template email'
        verbose_name_plural = 'Templates email'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class EmailLog(models.Model):
    """Historique des emails envoyés"""

    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('SENT', 'Envoyé'),
        ('FAILED', 'Échoué'),
        ('BOUNCED', 'Rebond'),
    )

    recipient_email = models.EmailField(verbose_name='Destinataire')
    recipient_name = models.CharField(max_length=255, blank=True, verbose_name='Nom destinataire')

    subject = models.CharField(max_length=255, verbose_name='Sujet')
    body_html = models.TextField(verbose_name='Corps HTML')
    body_text = models.TextField(blank=True, verbose_name='Corps texte')

    template_used = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Template utilisé'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='Statut')

    # Métadonnées
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Envoyé le')
    error_message = models.TextField(blank=True, verbose_name='Message d\'erreur')
    provider = models.CharField(max_length=50, blank=True, verbose_name='Fournisseur')

    # Tracking
    opened_at = models.DateTimeField(null=True, blank=True, verbose_name='Ouvert le')
    clicked_at = models.DateTimeField(null=True, blank=True, verbose_name='Cliqué le')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log email'
        verbose_name_plural = 'Logs email'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_email', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.recipient_email} - {self.subject} ({self.get_status_display()})"


class SMSTemplate(models.Model):
    """Template SMS réutilisable"""

    TEMPLATE_TYPE_CHOICES = (
        ('COMPLAINT_CREATED', 'Plainte créée'),
        ('STATUS_UPDATE', 'Mise à jour'),
        ('APPOINTMENT_REMINDER', 'Rappel RDV'),
        ('VERIFICATION_CODE', 'Code vérification'),
        ('ALERT', 'Alerte'),
        ('CUSTOM', 'Personnalisé'),
    )

    name = models.CharField(max_length=255, unique=True, verbose_name='Nom du template')
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPE_CHOICES, verbose_name='Type')

    content = models.TextField(max_length=160, verbose_name='Contenu SMS (max 160 car)')

    available_variables = models.JSONField(default=list, blank=True, verbose_name='Variables disponibles')

    is_active = models.BooleanField(default=True, verbose_name='Actif')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Template SMS'
        verbose_name_plural = 'Templates SMS'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class SMSLog(models.Model):
    """Historique des SMS envoyés"""

    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('SENT', 'Envoyé'),
        ('DELIVERED', 'Délivré'),
        ('FAILED', 'Échoué'),
    )

    recipient_phone = models.CharField(max_length=20, verbose_name='Téléphone destinataire')
    recipient_name = models.CharField(max_length=255, blank=True, verbose_name='Nom destinataire')

    content = models.TextField(max_length=160, verbose_name='Contenu')

    template_used = models.ForeignKey(
        SMSTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Template utilisé'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='Statut')

    # Métadonnées
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Envoyé le')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='Délivré le')
    error_message = models.TextField(blank=True, verbose_name='Message d\'erreur')
    provider = models.CharField(max_length=50, blank=True, verbose_name='Fournisseur')
    provider_message_id = models.CharField(max_length=255, blank=True, verbose_name='ID message fournisseur')

    # Coût
    cost = models.DecimalField(max_digits=6, decimal_places=4, default=0, verbose_name='Coût')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log SMS'
        verbose_name_plural = 'Logs SMS'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_phone', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.recipient_phone} - {self.content[:30]} ({self.get_status_display()})"


class NotificationQueue(models.Model):
    """File d'attente des notifications"""

    TYPE_CHOICES = (
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push'),
    )

    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='Type')

    recipient_id = models.IntegerField(verbose_name='ID destinataire')
    recipient_email = models.EmailField(blank=True, verbose_name='Email')
    recipient_phone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')

    template_name = models.CharField(max_length=255, verbose_name='Nom du template')
    context_data = models.JSONField(default=dict, verbose_name='Données contextuelles')

    priority = models.IntegerField(default=5, verbose_name='Priorité (1=haute, 10=basse)')

    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name='Programmé pour')

    processed = models.BooleanField(default=False, verbose_name='Traité')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Traité le')

    retry_count = models.IntegerField(default=0, verbose_name='Nombre de tentatives')
    max_retries = models.IntegerField(default=3, verbose_name='Tentatives max')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'File notification'
        verbose_name_plural = 'File notifications'
        ordering = ['priority', 'created_at']
        indexes = [
            models.Index(fields=['processed', 'priority']),
            models.Index(fields=['scheduled_at']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.template_name} ({self.recipient_email or self.recipient_phone})"

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
import pyotp


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'adresse email est obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser doit avoir is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('EMPLOYE', 'Employé'),
        ('EMPLOYE_MAISON', 'Employé de Maison'),
        ('EMPLOYEUR', 'Employeur'),
        ('INSPECTEUR', 'Inspecteur'),
        ('CHEF_INSPECTION', 'Chef d\'Inspection'),
        ('DIRECTEUR_REGIONAL', 'Directeur Régional'),
        ('DIRECTEUR_GENERAL', 'Directeur Général'),
        ('ADMIN', 'Administrateur'),
    )

    GENDER_CHOICES = (
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('O', 'Autre'),
    )

    email = models.EmailField(unique=True, verbose_name='Email')
    phone_number = PhoneNumberField(unique=True, null=True, blank=True, verbose_name='Numéro de téléphone')

    first_name = models.CharField(max_length=100, verbose_name='Prénom')
    last_name = models.CharField(max_length=100, verbose_name='Nom')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, verbose_name='Genre')
    date_of_birth = models.DateField(null=True, blank=True, verbose_name='Date de naissance')

    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True, verbose_name='Photo de profil')

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, verbose_name='Type d\'utilisateur')

    is_active = models.BooleanField(default=False, verbose_name='Actif')
    is_staff = models.BooleanField(default=False, verbose_name='Staff')
    is_verified = models.BooleanField(default=False, verbose_name='Vérifié')

    otp_secret = models.CharField(max_length=32, blank=True, verbose_name='Secret OTP')
    otp_enabled = models.BooleanField(default=False, verbose_name='OTP activé')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Date de modification')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='Dernière connexion')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    def generate_otp_secret(self):
        if not self.otp_secret:
            self.otp_secret = pyotp.random_base32()
            self.save()
        return self.otp_secret

    def get_otp_uri(self):
        return pyotp.totp.TOTP(self.otp_secret).provisioning_uri(
            name=self.email,
            issuer_name='Plateforme Travail'
        )

    def verify_otp(self, token):
        if not self.otp_enabled or not self.otp_secret:
            return False
        totp = pyotp.TOTP(self.otp_secret)
        return totp.verify(token, valid_window=1)


class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')

    national_id = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name='CNI')
    address = models.TextField(blank=True, verbose_name='Adresse')
    city = models.CharField(max_length=100, blank=True, verbose_name='Ville')

    job_title = models.CharField(max_length=200, blank=True, verbose_name='Poste')
    hire_date = models.DateField(null=True, blank=True, verbose_name='Date d\'embauche')

    current_employer = models.ForeignKey(
        'enterprises.Enterprise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name='Employeur actuel'
    )

    employment_contract = models.FileField(upload_to='contracts/', null=True, blank=True, verbose_name='Contrat de travail')

    # Inspecteur assigné — indépendant de tout contrat
    assigned_inspector = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='supervised_employees',
        verbose_name='Inspecteur assigné',
        limit_choices_to={'user_type__in': ['INSPECTEUR', 'CHEF_INSPECTION']},
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil Employé'
        verbose_name_plural = 'Profils Employés'

    def __str__(self):
        return f"Profil de {self.user.get_full_name()}"


class InspectorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='inspector_profile')

    badge_number = models.CharField(max_length=50, unique=True, verbose_name='Numéro de badge')
    inspection_zone = models.ForeignKey(
        'inspections.InspectionZone',
        on_delete=models.SET_NULL,
        null=True,
        related_name='inspectors',
        verbose_name='Zone d\'inspection'
    )

    specialization = models.CharField(max_length=200, blank=True, verbose_name='Spécialisation')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil Inspecteur'
        verbose_name_plural = 'Profils Inspecteurs'

    def __str__(self):
        return f"Inspecteur {self.user.get_full_name()} - {self.badge_number}"


class EmployerProfile(models.Model):
    EMPLOYER_TYPE_CHOICES = (
        ('ENTERPRISE', 'Entreprise'),
        ('AGENCY', 'Agence'),
        ('INDIVIDUAL', 'Particulier'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_profile')

    employer_type = models.CharField(max_length=20, choices=EMPLOYER_TYPE_CHOICES, verbose_name='Type d\'employeur')
    enterprise = models.ForeignKey(
        'enterprises.Enterprise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employer_profiles',
        verbose_name='Entreprise'
    )

    position = models.CharField(max_length=200, blank=True, verbose_name='Fonction')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil Employeur'
        verbose_name_plural = 'Profils Employeurs'

    def __str__(self):
        return f"Employeur {self.user.get_full_name()}"


class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Réinitialisation de mot de passe'
        verbose_name_plural = 'Réinitialisations de mot de passe'
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset pour {self.user.email} - {self.created_at}"

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Vérification d\'email'
        verbose_name_plural = 'Vérifications d\'email'
        ordering = ['-created_at']

    def __str__(self):
        return f"Vérification pour {self.user.email} - {self.created_at}"

    def is_valid(self):
        return not self.verified and timezone.now() < self.expires_at

from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class NewsArticle(models.Model):
    """Article d'actualite"""

    CATEGORY_CHOICES = (
        ('COMMUNIQUE', 'Communique'),
        ('REFORM', 'Reforme'),
        ('EVENT', 'Evenement'),
        ('CAMPAIGN', 'Campagne de sensibilisation'),
    )

    title = models.CharField(max_length=255, verbose_name='Titre')
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    excerpt = models.TextField(verbose_name='Extrait')
    content = models.TextField(verbose_name='Contenu')
    image = models.ImageField(upload_to='news/', null=True, blank=True, verbose_name='Image')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='COMMUNIQUE')
    author = models.CharField(max_length=100, verbose_name='Auteur')
    published_at = models.DateTimeField(default=timezone.now, verbose_name='Date de publication')
    is_featured = models.BooleanField(default=False, verbose_name='A la une')
    views = models.IntegerField(default=0, verbose_name='Nombre de vues')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Article d'actualite"
        verbose_name_plural = "Articles d'actualite"
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class FAQ(models.Model):
    """Questions frequemment posees"""

    category = models.CharField(max_length=100, verbose_name='Categorie')
    question = models.CharField(max_length=500, verbose_name='Question')
    answer = models.TextField(verbose_name='Reponse')
    order = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['category', 'order']

    def __str__(self):
        return self.question


class ResourceDocument(models.Model):
    """Document de ressource telechargeable"""

    CATEGORY_CHOICES = (
        ('CODE_TRAVAIL', 'Code du Travail'),
        ('GUIDE', 'Guide pratique'),
        ('CONVENTION', 'Convention collective'),
        ('CONTRACT_MODEL', 'Modele de contrat'),
        ('OTHER', 'Autre'),
    )

    title = models.CharField(max_length=255, verbose_name='Titre')
    description = models.TextField(verbose_name='Description')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    file = models.FileField(upload_to='resources/', verbose_name='Fichier')
    file_size = models.IntegerField(default=0, verbose_name='Taille du fichier (bytes)')
    downloads = models.IntegerField(default=0, verbose_name='Nombre de telechargements')
    published_at = models.DateTimeField(default=timezone.now, verbose_name='Date de publication')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Document de ressource'
        verbose_name_plural = 'Documents de ressources'
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class Testimonial(models.Model):
    """Temoignage d'utilisateur"""

    author_name = models.CharField(max_length=100, verbose_name='Nom')
    author_role = models.CharField(max_length=100, verbose_name='Role/Fonction')
    content = models.TextField(verbose_name='Temoignage')
    rating = models.IntegerField(default=5, verbose_name='Note (1-5)')
    published_at = models.DateTimeField(default=timezone.now, verbose_name='Date de publication')
    is_approved = models.BooleanField(default=False, verbose_name='Approuve')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Temoignage'
        verbose_name_plural = 'Temoignages'
        ordering = ['-published_at']

    def __str__(self):
        return f"{self.author_name} - {self.rating}/5"


class Campaign(models.Model):
    """Campagne de sensibilisation"""

    title = models.CharField(max_length=255, verbose_name='Titre')
    description = models.TextField(verbose_name='Description')
    image = models.ImageField(upload_to='campaigns/', verbose_name='Image')
    start_date = models.DateField(verbose_name='Date de debut')
    end_date = models.DateField(verbose_name='Date de fin')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Campagne'
        verbose_name_plural = 'Campagnes'
        ordering = ['-start_date']

    def __str__(self):
        return self.title


class PressRelease(models.Model):
    """Communique de presse"""

    title = models.CharField(max_length=255, verbose_name='Titre')
    content = models.TextField(verbose_name='Contenu')
    published_at = models.DateTimeField(default=timezone.now, verbose_name='Date de publication')
    contact_person = models.CharField(max_length=100, verbose_name='Personne de contact')
    contact_email = models.EmailField(verbose_name='Email de contact')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Communique de presse'
        verbose_name_plural = 'Communiques de presse'
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class PressAttachment(models.Model):
    """Piece jointe d'un communique de presse"""

    press_release = models.ForeignKey(
        PressRelease,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Communique de presse'
    )
    file = models.FileField(upload_to='press/', verbose_name='Fichier')
    title = models.CharField(max_length=255, verbose_name='Titre')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Piece jointe'
        verbose_name_plural = 'Pieces jointes'

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    """Message de contact depuis le site"""

    name = models.CharField(max_length=100, verbose_name='Nom')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, verbose_name='Telephone')
    subject = models.CharField(max_length=255, verbose_name='Sujet')
    message = models.TextField(verbose_name='Message')
    is_read = models.BooleanField(default=False, verbose_name='Lu')
    is_replied = models.BooleanField(default=False, verbose_name='Repondu')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class InspectionOffice(models.Model):
    """Bureau d'inspection du travail"""

    TYPE_CHOICES = (
        ('REGIONAL', 'Direction Regionale'),
        ('DEPARTMENTAL', 'Inspection Departementale'),
    )

    name = models.CharField(max_length=255, verbose_name='Nom')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='DEPARTMENTAL')
    address = models.TextField(verbose_name='Adresse')
    phone = models.CharField(max_length=20, verbose_name='Telephone')
    email = models.EmailField(verbose_name='Email')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Latitude')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Longitude')
    region = models.CharField(max_length=100, verbose_name='Region')
    city = models.CharField(max_length=100, verbose_name='Ville')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bureau d'inspection"
        verbose_name_plural = "Bureaux d'inspection"
        ordering = ['region', 'name']

    def __str__(self):
        return f"{self.name} - {self.region}"


class AIKeywordResponse(models.Model):
    """Reponse predefinie de l'assistant IA basee sur mots-cles"""

    keyword = models.CharField(max_length=100, unique=True, verbose_name='Mot-cle')
    question_example = models.CharField(max_length=255, verbose_name='Exemple de question')
    response = models.TextField(verbose_name='Reponse')
    priority = models.IntegerField(default=0, verbose_name='Priorite (0=plus haute)')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Reponse IA'
        verbose_name_plural = 'Reponses IA'
        ordering = ['priority', 'keyword']

    def __str__(self):
        return f"{self.keyword} - {self.question_example[:50]}"

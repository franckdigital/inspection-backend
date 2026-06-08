import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

email = "admin@travail.cg"
password = "admin123"

if not User.objects.filter(email=email).exists():
    user = User.objects.create_superuser(
        email=email,
        password=password,
        first_name="Admin",
        last_name="Système",
        user_type="ADMIN"
    )
    user.is_verified = True
    user.is_active = True
    user.save()
    print(f"Superutilisateur créé: {email} / {password}")
else:
    print("Le superutilisateur existe déjà")

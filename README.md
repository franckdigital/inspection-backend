# Backend - API Plateforme Nationale de Gestion du Travail

API Django REST Framework pour la plateforme de gestion des inspections du travail.

## Technologies ok

- **Framework**: Django 6.0.5
- **API**: Django REST Framework 3.15.1
- **Base de données**: MySQL
- **Authentification**: JWT (Simple JWT)
- **Documentation**: drf-spectacular (Swagger/ReDoc)

## Installation

### 1. Environnement virtuel

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration

Créez un fichier `.env` à la racine du backend en vous basant sur `.env.example` :

```env
DB_NAME=travail
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
```

### 4. Base de données

Créez la base de données MySQL :

```sql
CREATE DATABASE travail CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Puis lancez les migrations :

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Créer un superutilisateur

```bash
python manage.py createsuperuser
```

### 6. Lancer le serveur

```bash
python manage.py runserver
```

L'API sera accessible sur `http://localhost:8000`

## Modules implémentés

### LOT 2 : Gestion des utilisateurs (`users/`)

**Modèles** :
- `User` : Utilisateur personnalisé avec types (EMPLOYE, EMPLOYEUR, INSPECTEUR, etc.)
- `EmployeeProfile` : Profil employé
- `InspectorProfile` : Profil inspecteur
- `EmployerProfile` : Profil employeur
- `PasswordReset` : Gestion réinitialisation mot de passe
- `EmailVerification` : Vérification email

**Endpoints** :
- `POST /api/users/register/` : Inscription
- `POST /api/users/login/` : Connexion (retourne JWT)
- `POST /api/users/token/refresh/` : Rafraîchir le token
- `GET /api/users/me/` : Profil utilisateur
- `PUT /api/users/me/` : Mettre à jour le profil
- `POST /api/users/change-password/` : Changer le mot de passe
- `POST /api/users/password-reset/` : Demander réinitialisation
- `POST /api/users/password-reset/confirm/` : Confirmer réinitialisation
- `POST /api/users/verify-email/` : Vérifier email
- `GET /api/users/otp/setup/` : Configurer OTP/2FA
- `POST /api/users/otp/setup/` : Activer OTP
- `POST /api/users/otp/verify/` : Vérifier code OTP
- `POST /api/users/otp/disable/` : Désactiver OTP

### LOT 3 : Registre des entreprises (`enterprises/`)

**Modèles** :
- `Enterprise` : Entreprise avec RCCM, NIF, scoring
- `EnterpriseBranch` : Succursales
- `EnterpriseDocument` : Documents (RCCM, statuts, etc.)
- `EnterpriseHistory` : Historique événements

**Endpoints** :
- `GET /api/enterprises/` : Liste des entreprises (filtrable, recherche)
- `POST /api/enterprises/` : Créer une entreprise
- `GET /api/enterprises/{id}/` : Détails entreprise
- `PUT /api/enterprises/{id}/` : Mettre à jour
- `DELETE /api/enterprises/{id}/` : Supprimer
- `GET /api/enterprises/{id}/branches/` : Liste succursales
- `GET /api/enterprises/{id}/documents/` : Liste documents
- `GET /api/enterprises/{id}/history/` : Historique
- `POST /api/enterprises/{id}/update_score/` : Recalculer score conformité

### LOT 4 : Gestion des plaintes (`complaints/`)

**Modèles** :
- `Complaint` : Plainte avec workflow, statuts, priorités
- `ComplaintDocument` : Documents joints (contrat, photos, vidéos, audio)
- `ComplaintComment` : Commentaires et échanges
- `ComplaintStatusHistory` : Historique des changements de statut
- `ComplaintNotification` : Notifications

**Endpoints** :
- `GET /api/complaints/` : Liste plaintes (filtrée selon le profil)
- `POST /api/complaints/` : Déposer une plainte
- `GET /api/complaints/{id}/` : Détails plainte
- `POST /api/complaints/{id}/assign/` : Assigner à un inspecteur
- `POST /api/complaints/{id}/update_status/` : Changer le statut
- `GET /api/complaints/{id}/documents/` : Documents de la plainte
- `POST /api/complaints/{id}/add_document/` : Ajouter un document
- `GET /api/complaints/{id}/comments/` : Commentaires
- `POST /api/complaints/{id}/add_comment/` : Ajouter un commentaire
- `GET /api/complaints/notifications/` : Notifications utilisateur
- `POST /api/complaints/notifications/{id}/mark_as_read/` : Marquer comme lu

### Zones d'inspection (`inspections/`)

**Modèles** :
- `InspectionZone` : Zones géographiques d'inspection
- `InspectionRecord` : Enregistrements d'inspections

## Documentation API

Une fois le serveur lancé, accédez à :

- **Swagger UI** : `http://localhost:8000/api/docs/`
- **ReDoc** : `http://localhost:8000/api/redoc/`
- **Schéma OpenAPI** : `http://localhost:8000/api/schema/`

## Admin Django

Interface d'administration : `http://localhost:8000/admin/`

Connectez-vous avec le superutilisateur créé précédemment.

## Authentification

L'API utilise JWT (JSON Web Tokens) :

1. Connexion : `POST /api/users/login/`
   ```json
   {
     "email": "user@example.com",
     "password": "password123"
   }
   ```

2. Réponse :
   ```json
   {
     "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "user": {...}
   }
   ```

3. Utiliser le token dans les requêtes :
   ```
   Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
   ```

## Permissions et accès

- **EMPLOYE** : Peut créer des plaintes, voir ses propres plaintes
- **EMPLOYEUR** : Peut gérer son entreprise, répondre aux plaintes
- **INSPECTEUR** : Peut voir les plaintes assignées, mener des enquêtes
- **CHEF_INSPECTION** : Supervision zone, réaffectation
- **DIRECTEUR_REGIONAL** : Vue régionale
- **DIRECTEUR_GENERAL** : Vue nationale complète
- **ADMIN** : Accès total

## Développement

### Structure des apps

```
backend/
├── config/              # Configuration Django
├── users/              # LOT 2 - Utilisateurs
├── enterprises/        # LOT 3 - Entreprises
├── complaints/         # LOT 4 - Plaintes
├── inspections/        # LOT 5 - Inspections
├── mediations/         # LOT 7 - Médiations
├── media/              # Fichiers uploadés
└── staticfiles/        # Fichiers statiques
```

### Tests

```bash
python manage.py test
```

## Production

Pour la production, configurez :

1. `DEBUG = False` dans settings
2. Configurez `ALLOWED_HOSTS`
3. Utilisez un serveur de production (Gunicorn + Nginx)
4. Configurez les emails SMTP
5. Utilisez un stockage distant (AWS S3) pour les fichiers
6. Configurez Redis pour Celery

## Prochaines étapes

- [ ] Implémenter LOT 5 : Workflow complet inspecteurs
- [ ] Implémenter LOT 6 : Gestion hiérarchique
- [ ] Implémenter LOT 7 : Médiation et conciliation
- [ ] Implémenter LOT 9 : Employés de maison
- [ ] Ajouter les tests unitaires et d'intégration
- [ ] Configurer Celery pour les tâches asynchrones
- [ ] Ajouter WebSockets (Channels) pour notifications temps réel

## Support

Pour toute question : numerix.digital@gmail.com

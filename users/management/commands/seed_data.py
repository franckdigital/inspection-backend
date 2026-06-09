"""
python manage.py seed_data

Données de démonstration complètes :
  - 1 Chef d'inspection + 10 Inspecteurs (2 par zone)
  - 5 Zones d'inspection avec affectations (InspectorZoneAssignment)
  - 5 Entreprises + 5 Salariés (EMPLOYE)
  - 5 Patrons (EMPLOYEUR) + 5 Employés de maison (EMPLOYE_MAISON)
  - 10 Plaintes écrites (EMPLOYE + EMPLOYE_MAISON, tous statuts)
  - 5 Plaintes vocales (EMPLOYE_MAISON, langues locales)
  - 10 Enregistrements d'inspection / planning inspecteurs
  - 3 Médiations + 2 Procédures judiciaires
  - Affectation inspecteur → employé de maison + employé salarié
"""

from datetime import date, time, timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import transaction

NOW = timezone.now()

# ─── Données de référence ─────────────────────────────────────────────────────

LANGUAGES = [
    ('DIOULA',  'Dioula',  'Bouaké',       'Vallée du Bandama', '7.6900', '-5.0300'),
    ('BAOULE',  'Baoulé',  'Yamoussoukro', 'Lacs',              '6.8200', '-5.2700'),
    ('BETE',    'Bété',    'Daloa',        'Haut-Sassandra',    '6.8700', '-6.4500'),
    ('SENOUFO', 'Sénoufo', 'Korhogo',      'Poro',              '9.4600', '-5.6300'),
    ('ANYIN',   'Anyin',   'Abengourou',   'Indénié-Djuablin',  '6.7300', '-3.4900'),
]

INSPECTOR_NAMES = [
    ('Mamadou',  'Coulibaly'), ('Ibrahim',  'Traoré'),    # Dioula
    ('Kouassi',  'Konan'),     ('Akissi',   'Assoumou'),  # Baoulé
    ('Gnagno',   'Gbagbo'),    ('Séraphin', 'Daho'),      # Bété
    ('Navigué',  'Silué'),     ('Dramane',  'Koné'),      # Sénoufo
    ('Adjoua',   'Assi'),      ('Konan',    'Attia'),     # Anyin
]

ENTERPRISE_DATA = [
    {
        'name': 'SIVOCI Industrie SA',        'legal_form': 'SA',
        'rccm': 'CI-ABJ-2018-B-04521',        'nif': 'CI-2018-00041',
        'sector': 'INDUSTRIE',
        'headquarters_address': 'Zone Industrielle de Yopougon, Lot 47',
        'city': 'Abidjan', 'region': 'Lagunes',
        'phone': '+2252722345001', 'email': 'contact@sivoci.ci',
        'employee_count': 210, 'founding_date': date(2018, 3, 15),
        'lat': '5.3600', 'lng': '-4.0083',
    },
    {
        'name': 'Groupe Agro-CI SARL',        'legal_form': 'SARL',
        'rccm': 'CI-ABJ-2015-B-01873',        'nif': 'CI-2015-00082',
        'sector': 'AGRICULTURE',
        'headquarters_address': '12 Rue des Cacaoyères, Plateau',
        'city': 'Abidjan', 'region': 'Lagunes',
        'phone': '+2252722345002', 'email': 'info@agroci.ci',
        'employee_count': 85, 'founding_date': date(2015, 7, 20),
        'lat': '5.3197', 'lng': '-4.0167',
    },
    {
        'name': "TechPrime Côte d'Ivoire SAS", 'legal_form': 'SAS',
        'rccm': 'CI-ABJ-2020-B-07732',         'nif': 'CI-2020-00153',
        'sector': 'TECHNOLOGIE',
        'headquarters_address': 'Immeuble Star 3, Avenue Lamblin',
        'city': 'Abidjan', 'region': 'Lagunes',
        'phone': '+2252722345003', 'email': 'hello@techprime.ci',
        'employee_count': 47, 'founding_date': date(2020, 1, 8),
        'lat': '5.3215', 'lng': '-4.0183',
    },
    {
        'name': 'Hôtel Savane Palace',         'legal_form': 'SARL',
        'rccm': 'CI-BKE-2012-B-00334',         'nif': 'CI-2012-00217',
        'sector': 'HOTELLERIE',
        'headquarters_address': 'Avenue de la République, Quartier Commerce',
        'city': 'Bouaké', 'region': 'Vallée du Bandama',
        'phone': '+2252722345004', 'email': 'reservation@savaneci.ci',
        'employee_count': 130, 'founding_date': date(2012, 11, 1),
        'lat': '7.6833', 'lng': '-5.0333',
    },
    {
        'name': 'BTP Construction Daloa',      'legal_form': 'EI',
        'rccm': 'CI-DAL-2017-B-00891',         'nif': 'CI-2017-00398',
        'sector': 'CONSTRUCTION',
        'headquarters_address': 'Route de Vavoua, km 4',
        'city': 'Daloa', 'region': 'Haut-Sassandra',
        'phone': '+2252722345005', 'email': 'direction@btpdaloa.ci',
        'employee_count': 65, 'founding_date': date(2017, 5, 14),
        'lat': '6.8770', 'lng': '-6.4502',
    },
]

EMPLOYEE_DATA = [
    ('Fofana',    'Lassina',  'M', '1990-04-12', 'Technicien de production',  '2021-03-01', 'Abidjan', '225060100001'),
    ('Ouédraogo', 'Awa',      'F', '1994-08-25', 'Responsable qualité',       '2020-07-15', 'Abidjan', '225060100002'),
    ("N'Goran",   'Serge',    'M', '1988-12-05', 'Agronome terrain',          '2019-01-10', 'Abidjan', '225060100003'),
    ('Koffi',     'Amenan',   'F', '1996-02-18', 'Développeur fullstack',     '2022-06-01', 'Abidjan', '225060100004'),
    ('Ouattara',  'Issouf',   'M', '1985-09-30', 'Chef de chantier',          '2018-11-20', 'Bouaké',  '225060100005'),
]

PATRON_DATA = [
    ('Diabaté',   'Fatoumata', 'F', '1975-03-10', 'Cocody, Rue des Jardins 14',         'Abidjan', '5.3600', '-3.9900', '225070200001'),
    ('Bamba',     'Drissa',    'M', '1968-07-22', 'Marcory, Rue du Commerce 7',          'Abidjan', '5.2900', '-4.0000', '225070200002'),
    ('Ettien',    'Clarisse',  'F', '1980-11-05', 'Plateau, Avenue Chardy 3',            'Abidjan', '5.3197', '-4.0167', '225070200003'),
    ('Coulibaly', 'Adama',     'M', '1972-01-30', "Quartier Kôkô, Résidence Forêt 2",   'Korhogo', '9.4590', '-5.6290', '225070200004'),
    ('Konan',     'Evelyne',   'F', '1983-06-14', 'Quartier Air France, Villa 8',        'Bouaké',  '7.6880', '-5.0210', '225070200005'),
]

WORKER_DATA = [
    ('Sanogo',   'Aminata', 'F', '2000-05-20', 'HOUSEKEEPER', 3, 'Abobo, Cité Belle Vie',       'Abidjan', '225080300001', 'DIOULA'),
    ('Traoré',   'Mariam',  'F', '1998-09-08', 'COOK',        5, 'Yopougon, Quartier Kennedy',  'Abidjan', '225080300002', 'BAOULE'),
    ('Bah',      'Mamou',   'F', '2002-01-15', 'NANNY',       2, 'Treichville, Rue 10',          'Abidjan', '225080300003', 'BETE'),
    ('Bakayoko', 'Seydou',  'M', '1997-04-03', 'GARDENER',    4, 'Quartier Kôkô Sud',            'Korhogo', '225080300004', 'SENOUFO'),
    ('Yao',      'Akissi',  'F', '2001-11-28', 'GENERAL',     1, 'Quartier Air France',          'Bouaké',  '225080300005', 'ANYIN'),
]

# Plaintes employés salariés
EMPLOYEE_COMPLAINTS = [
    ('UNPAID_SALARY',      'Salaires impayés depuis 3 mois',             'ASSIGNED',           'HIGH',   'Yopougon Industrie, Zone 3',        '5.3556', '-4.0700'),
    ('HARASSMENT',         'Harcèlement moral par supérieur hiérarchique','IN_PROGRESS',        'URGENT', 'Plateau, Bureau direction',         '5.3200', '-4.0200'),
    ('TERMINATION',        'Licenciement abusif sans motif valable',     'UNDER_INVESTIGATION','HIGH',   'Zone Industrielle Vridi',           '5.2500', '-3.9700'),
    ('WORKING_CONDITIONS', 'Absence de protections individuelles EPI',   'MEDIATION',          'MEDIUM', 'Route de Vavoua, km 4',             '6.8770', '-6.4502'),
    ('OVERTIME',           'Heures supplémentaires non rémunérées',      'PENDING',            'MEDIUM', 'Avenue Lamblin, Immeuble Star 3',   '5.3215', '-4.0183'),
    ('CONTRACT',           'Contrat non respecté — modification unilatérale', 'RESOLVED',      'LOW',    'Yamoussoukro, Zone commerciale',    '6.8200', '-5.2700'),
    ('DISCRIMINATION',     'Discrimination à la promotion pour raison ethnique', 'CLOSED',     'LOW',    'Bouaké, Avenue de la République',   '7.6833', '-5.0333'),
    ('ACCIDENT',           'Accident de travail non déclaré par employeur', 'ESCALATED',       'URGENT', 'Daloa, Chantier route nationale',   '6.8770', '-6.4502'),
]

# Plaintes employés de maison
DOMESTIC_COMPLAINTS = [
    ('UNPAID_SALARY',      'Patron refuse de payer le salaire du mois',         'ASSIGNED',           'HIGH',   'Cocody, Rue des Jardins 14',   '5.3600', '-3.9900'),
    ('WORKING_CONDITIONS', 'Conditions de travail dégradantes, 16h par jour',   'IN_PROGRESS',        'URGENT', 'Marcory, Rue du Commerce 7',  '5.2900', '-4.0000'),
    ('CONTRACT',           'Aucun contrat écrit établi malgré demandes répétées','UNDER_INVESTIGATION','MEDIUM', 'Plateau, Avenue Chardy 3',    '5.3197', '-4.0167'),
    ('HARASSMENT',         'Harcèlement et violences verbales du patron',        'MEDIATION',          'HIGH',   'Korhogo, Résidence Forêt 2',  '9.4590', '-5.6290'),
    ('TERMINATION',        'Renvoi immédiat sans préavis ni indemnité',          'PENDING',            'MEDIUM', 'Bouaké, Villa Air France',    '7.6880', '-5.0210'),
]

# Plaintes vocales employés de maison
VOICE_COMPLAINT_DATA = [
    ('Aminata Sanogo',   'Fatoumata Diabaté',  'DIOULA',  'Cocody',      '5.3600', '-3.9900', 'ASSIGNED'),
    ('Mariam Traoré',    'Drissa Bamba',        'BAOULE',  'Marcory',     '5.2900', '-4.0000', 'IN_PROGRESS'),
    ('Mamou Bah',        'Clarisse Ettien',     'BETE',    'Plateau',     '5.3197', '-4.0167', 'PENDING'),
    ('Seydou Bakayoko',  'Adama Coulibaly',     'SENOUFO', 'Korhogo',     '9.4590', '-5.6290', 'ASSISTANCE_REQUESTED'),
    ('Akissi Yao',       'Evelyne Konan',       'ANYIN',   'Bouaké',      '7.6880', '-5.0210', 'PENDING'),
]

# Planning d'inspections (passées + futures)
INSPECTION_PLANNING = [
    # (entreprise_idx, inspecteur_idx, type, jours_delta, terminée, résultat, constats)
    (0, 0, 'ROUTINE',    -30, True,  'COMPLIANT',      'Visite de routine. Conditions de travail conformes. Registre du personnel à jour. Affichage réglementaire en place.'),
    (1, 1, 'COMPLAINT',  -15, True,  'MINOR_ISSUES',   'Suite plainte PLT-2024-001. Constat de retards de paiement sur 2 mois. Mise en demeure adressée. Délai accordé pour régularisation.'),
    (2, 2, 'SPOT_CHECK', -7,  True,  'MAJOR_ISSUES',   'Contrôle inopiné. Absence de fiches de paie pour 12 employés. Non-respect des horaires légaux. PV dressé. Suite judiciaire envisagée.'),
    (3, 3, 'ROUTINE',    -45, True,  'COMPLIANT',      'Inspection annuelle. Conformité générale satisfaisante. Document unique de prévention à actualiser avant le 30/06.'),
    (4, 4, 'FOLLOW_UP',  -5,  True,  'NON_COMPLIANT',  "Visite de suivi post-PV. L'entreprise n'a pas régularisé les manquements constatés. Saisine de la Direction régionale."),
    (0, 0, 'COMPLAINT',  +7,  False, 'COMPLIANT',      'Inspection programmée suite à plainte pour harcèlement. En attente de réalisation.'),
    (1, 1, 'ROUTINE',    +14, False, 'COMPLIANT',      'Inspection de routine annuelle programmée. En attente de réalisation.'),
    (2, 2, 'FOLLOW_UP',  +21, False, 'COMPLIANT',      'Visite de suivi des mesures correctives demandées. En attente de réalisation.'),
    (3, 3, 'SPOT_CHECK', +3,  False, 'COMPLIANT',      'Contrôle inopiné programmé suite à signalement anonyme. En attente de réalisation.'),
    (4, 4, 'ROUTINE',    +30, False, 'COMPLIANT',      'Inspection semestrielle programmée. En attente de réalisation.'),
]


class Command(BaseCommand):
    help = 'Seed données complètes : inspecteurs, entreprises, travailleurs, plaintes, planning'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Seed données démo ==='))
        try:
            with transaction.atomic():
                zones      = self._create_zones()
                chef       = self._create_chef_inspection(zones)
                inspectors = self._create_inspectors(zones, chef)
                self._create_zone_assignments(zones, inspectors)
                enterprises = self._create_enterprises()
                employees   = self._create_enterprise_employees(enterprises, inspectors)
                patrons     = self._create_domestic_patrons()
                workers     = self._create_domestic_workers(patrons, inspectors)
                complaints  = self._create_employee_complaints(employees, inspectors, enterprises)
                dom_complaints = self._create_domestic_complaints(workers, inspectors, patrons)
                self._create_voice_complaints(workers, inspectors)
                self._create_inspection_planning(enterprises, inspectors)
                self._create_mediations(complaints + dom_complaints, inspectors)
                self._create_judicial_procedures(complaints, inspectors)
            self.stdout.write(self.style.SUCCESS('\n✓ Seed terminé avec succès.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Seed échoué : {e}'))
            import traceback; traceback.print_exc()
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # ZONES
    # ──────────────────────────────────────────────────────────────────────────
    def _create_zones(self):
        from inspections.models import InspectionZone
        self.stdout.write('\n[Zones d\'inspection]')
        zones = {}
        for lang_code, lang_label, city, region, lat, lng in LANGUAGES:
            zone, created = InspectionZone.objects.get_or_create(
                code=f'ZONE-{lang_code}',
                defaults=dict(
                    name=f'Zone Inspection — {lang_label}',
                    region=region, city=city,
                    description=f'Zone desservant les communautés de langue {lang_label}',
                    latitude=lat, longitude=lng, is_active=True,
                ),
            )
            zones[lang_code] = zone
            self.stdout.write(f'  {"créée" if created else "existante"} → {zone.code}')
        return zones

    # ──────────────────────────────────────────────────────────────────────────
    # CHEF D'INSPECTION
    # ──────────────────────────────────────────────────────────────────────────
    def _create_chef_inspection(self, zones):
        from users.models import User, InspectorProfile
        self.stdout.write('\n[Chef d\'inspection]')
        user, created = User.objects.get_or_create(
            email='chef.inspection@meps.ci',
            defaults=dict(
                first_name='Daouda', last_name='Sangaré',
                user_type='CHEF_INSPECTION',
                phone_number='+2250100000000',
                gender='M', is_active=True, is_verified=True,
            ),
        )
        if created:
            user.set_password('Chef@2024!')
            user.save()
        InspectorProfile.objects.get_or_create(
            user=user,
            defaults=dict(
                badge_number='CHEF-CI-2024-000',
                inspection_zone=zones['DIOULA'],
                specialization='Droit du travail — Chef de service Abidjan',
            ),
        )
        # Affecter comme chef de la zone principale
        zones['DIOULA'].head_inspector = user
        zones['DIOULA'].save(update_fields=['head_inspector'])
        self.stdout.write(f'  {"créé" if created else "existant"} → {user.get_full_name()}')
        return user

    # ──────────────────────────────────────────────────────────────────────────
    # INSPECTEURS
    # ──────────────────────────────────────────────────────────────────────────
    def _create_inspectors(self, zones, chef):
        from users.models import User, InspectorProfile
        self.stdout.write('\n[Inspecteurs]')
        inspectors = []
        lang_keys = list(zones.keys())
        for idx, (last_name, first_name) in enumerate(INSPECTOR_NAMES):
            lang_code  = lang_keys[idx // 2]
            lang_label = LANGUAGES[idx // 2][1]
            email      = f'inspecteur.{first_name.lower()}.{last_name.lower()}@inspection.ci'
            user, created = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first_name, last_name=last_name,
                    user_type='INSPECTEUR',
                    phone_number=f'+2250100{10 + idx:04d}',
                    gender='M' if idx % 3 != 1 else 'F',
                    is_active=True, is_verified=True,
                ),
            )
            if created:
                user.set_password('Inspect@2024!')
                user.save()
            InspectorProfile.objects.get_or_create(
                user=user,
                defaults=dict(
                    badge_number=f'INSP-CI-2024-{idx + 1:03d}',
                    inspection_zone=zones[lang_code],
                    specialization=f'Langue locale : {lang_label} — Droit du travail',
                ),
            )
            inspectors.append(user)
            self.stdout.write(f'  {"créé" if created else "existant"} → {user.get_full_name()} ({lang_label})')
        return inspectors

    # ──────────────────────────────────────────────────────────────────────────
    # AFFECTATIONS ZONE ↔ INSPECTEUR
    # ──────────────────────────────────────────────────────────────────────────
    def _create_zone_assignments(self, zones, inspectors):
        from inspections.models import InspectorZoneAssignment
        self.stdout.write('\n[Affectations zones]')
        lang_keys = list(zones.keys())
        for idx, inspector in enumerate(inspectors):
            lang_code = lang_keys[idx // 2]
            lang_label = LANGUAGES[idx // 2][1]
            zone = zones[lang_code]
            asgn, created = InspectorZoneAssignment.objects.get_or_create(
                zone=zone, inspector=inspector,
                defaults=dict(
                    role='MEMBER',
                    languages_spoken=[lang_code, 'FRENCH'],
                    is_active=True,
                ),
            )
            self.stdout.write(f'  {"créée" if created else "existante"} → {inspector.get_full_name()} → {zone.code}')

    # ──────────────────────────────────────────────────────────────────────────
    # ENTREPRISES
    # ──────────────────────────────────────────────────────────────────────────
    def _create_enterprises(self):
        from enterprises.models import Enterprise
        self.stdout.write('\n[Entreprises]')
        enterprises = []
        for d in ENTERPRISE_DATA:
            ent, created = Enterprise.objects.get_or_create(
                rccm=d['rccm'],
                defaults=dict(
                    name=d['name'], legal_form=d['legal_form'], nif=d['nif'],
                    sector=d['sector'],
                    headquarters_address=d['headquarters_address'],
                    city=d['city'], region=d['region'], country='CI',
                    phone_number=d['phone'], email=d['email'],
                    employee_count=d['employee_count'],
                    founding_date=d['founding_date'],
                    latitude=d['lat'], longitude=d['lng'],
                    compliance_score=70, risk_level='LOW',
                    is_active=True, is_verified=True,
                ),
            )
            enterprises.append(ent)
            self.stdout.write(f'  {"créée" if created else "existante"} → {ent.name}')
        return enterprises

    # ──────────────────────────────────────────────────────────────────────────
    # SALARIÉS (EMPLOYE)
    # ──────────────────────────────────────────────────────────────────────────
    def _create_enterprise_employees(self, enterprises, inspectors):
        from users.models import User, EmployeeProfile
        self.stdout.write('\n[Salariés (EMPLOYE)]')
        employees = []
        for idx, (last, first, gender, dob, title, hire, city, phone_sfx) in enumerate(EMPLOYEE_DATA):
            email = f'employe.{first.lower()}.{last.lower().replace("\'", "")}@work.ci'
            user, created = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first, last_name=last,
                    user_type='EMPLOYE',
                    phone_number=f'+{phone_sfx}',
                    gender=gender,
                    date_of_birth=date.fromisoformat(dob),
                    is_active=True, is_verified=True,
                ),
            )
            if created:
                user.set_password('Employe@2024!')
                user.save()
            enterprise = enterprises[idx % len(enterprises)]
            EmployeeProfile.objects.get_or_create(
                user=user,
                defaults=dict(
                    national_id=f'CI{2000 + idx:06d}',
                    address=f'Quartier résidentiel, Lot {100 + idx}',
                    city=city, job_title=title,
                    hire_date=date.fromisoformat(hire),
                    current_employer=enterprise,
                ),
            )
            employees.append(user)
            self.stdout.write(f'  {"créé" if created else "existant"} → {user.get_full_name()} ({enterprise.name})')
        return employees

    # ──────────────────────────────────────────────────────────────────────────
    # PATRONS (EMPLOYEUR)
    # ──────────────────────────────────────────────────────────────────────────
    def _create_domestic_patrons(self):
        from users.models import User
        from domestic.models import DomesticEmployer
        self.stdout.write('\n[Patrons (EMPLOYEUR)]')
        patrons = []
        for idx, (last, first, gender, dob, address, city, lat, lng, phone_sfx) in enumerate(PATRON_DATA):
            email = f'patron.{first.lower()}.{last.lower()}@famille.ci'
            user, created = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first, last_name=last,
                    user_type='EMPLOYEUR',
                    phone_number=f'+{phone_sfx}',
                    gender=gender,
                    date_of_birth=date.fromisoformat(dob),
                    is_active=True, is_verified=True,
                ),
            )
            if created:
                user.set_password('Patron@2024!')
                user.save()
            employer, _ = DomesticEmployer.objects.get_or_create(
                user=user,
                defaults=dict(
                    employer_type='INDIVIDUAL',
                    household_size=3 + idx % 3,
                    has_children=(idx % 2 == 0),
                    has_pets=(idx % 3 == 0),
                    address=address, city=city,
                    latitude=lat, longitude=lng,
                ),
            )
            patrons.append(employer)
            self.stdout.write(f'  {"créé" if created else "existant"} → {user.get_full_name()} ({city})')
        return patrons

    # ──────────────────────────────────────────────────────────────────────────
    # EMPLOYÉS DE MAISON (EMPLOYE_MAISON) + CONTRATS
    # ──────────────────────────────────────────────────────────────────────────
    def _create_domestic_workers(self, patrons, inspectors):
        from users.models import User
        from domestic.models import DomesticWorker, DomesticContract
        self.stdout.write('\n[Employés de maison (EMPLOYE_MAISON)]')
        workers = []
        for idx, (last, first, gender, dob, spec, exp, address, city, phone_sfx, lang) in enumerate(WORKER_DATA):
            email = f'employe.maison.{first.lower()}.{last.lower()}@travail.ci'
            user, created = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first, last_name=last,
                    user_type='EMPLOYE_MAISON',
                    phone_number=f'+{phone_sfx}',
                    gender=gender,
                    date_of_birth=date.fromisoformat(dob),
                    is_active=True, is_verified=True,
                ),
            )
            if created:
                user.set_password('Worker@2024!')
                user.save()

            # Affecter un inspecteur spécialisé dans la langue du travailleur
            assigned_insp = inspectors[idx * 2 % len(inspectors)]
            patron = patrons[idx % len(patrons)]
            worker, w_created = DomesticWorker.objects.get_or_create(
                user=user,
                defaults=dict(
                    specialization=spec,
                    years_experience=exp,
                    is_available=False,
                    preferred_work_days=['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi'],
                    assigned_inspector=assigned_insp,
                ),
            )
            if not w_created and worker.assigned_inspector is None:
                worker.assigned_inspector = assigned_insp
                worker.save(update_fields=['assigned_inspector'])

            DomesticContract.objects.get_or_create(
                worker=worker, employer=patron,
                defaults=dict(
                    status='ACTIVE',
                    start_date=date(2024, 1, 1 + idx * 30 % 28),
                    salary=75000 + idx * 5000,
                    currency='XOF',
                    payment_frequency='MONTHLY',
                    work_hours_start=time(7, 0),
                    work_hours_end=time(17, 0),
                    weekly_hours=45,
                    work_days=['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'],
                    days_off=['dimanche'],
                    tasks=['ménage', 'cuisine', 'lessive'],
                    annual_leave_days=15,
                ),
            )
            workers.append(worker)
            self.stdout.write(
                f'  {"créé" if created else "existant"} → {user.get_full_name()} → patron {patron.user.get_full_name()} '
                f'[inspecteur: {assigned_insp.get_full_name()}]'
            )
        return workers

    # ──────────────────────────────────────────────────────────────────────────
    # PLAINTES EMPLOYÉS SALARIÉS
    # ──────────────────────────────────────────────────────────────────────────
    def _create_employee_complaints(self, employees, inspectors, enterprises):
        from complaints.models import Complaint
        self.stdout.write('\n[Plaintes salariés (EMPLOYE)]')
        created_complaints = []
        for idx, (ctype, subject, status, priority, addr, lat, lng) in enumerate(EMPLOYEE_COMPLAINTS):
            complainant = employees[idx % len(employees)]
            inspector   = inspectors[idx % len(inspectors)]
            enterprise  = enterprises[idx % len(enterprises)]
            number = f'PLT-2024-{100 + idx:03d}'
            c, created = Complaint.objects.get_or_create(
                complaint_number=number,
                defaults=dict(
                    complainant=complainant,
                    complaint_type=ctype,
                    subject=subject,
                    description=f'Plainte déposée par {complainant.get_full_name()} concernant : {subject}. '
                                f'Les faits se sont déroulés sur le lieu de travail. '
                                f'Le plaignant demande une intervention urgente de l\'inspection du travail.',
                    enterprise=enterprise,
                    employer_name=enterprise.name,
                    workplace_address=addr,
                    workplace_latitude=lat,
                    workplace_longitude=lng,
                    incident_date=date.today() - timedelta(days=30 + idx * 7),
                    status=status,
                    priority=priority,
                    assigned_to=inspector if status != 'PENDING' else None,
                    resolution='Dossier en cours de traitement.' if status in ('RESOLVED', 'CLOSED') else '',
                ),
            )
            created_complaints.append(c)
            self.stdout.write(
                f'  {"créée" if created else "existante"} → {number} [{status}] '
                f'{complainant.get_full_name()} → insp. {inspector.get_full_name()}'
            )
        return created_complaints

    # ──────────────────────────────────────────────────────────────────────────
    # PLAINTES EMPLOYÉS DE MAISON
    # ──────────────────────────────────────────────────────────────────────────
    def _create_domestic_complaints(self, workers, inspectors, patrons):
        from complaints.models import Complaint
        self.stdout.write('\n[Plaintes employés de maison (EMPLOYE_MAISON)]')
        created_complaints = []
        for idx, (ctype, subject, status, priority, addr, lat, lng) in enumerate(DOMESTIC_COMPLAINTS):
            worker_obj  = workers[idx % len(workers)]
            complainant = worker_obj.user
            inspector   = worker_obj.assigned_inspector or inspectors[idx % len(inspectors)]
            patron      = patrons[idx % len(patrons)]
            number = f'DOM-PLT-2024-{200 + idx:03d}'
            c, created = Complaint.objects.get_or_create(
                complaint_number=number,
                defaults=dict(
                    complainant=complainant,
                    complaint_type=ctype,
                    subject=subject,
                    description=f'Plainte d\'employé(e) de maison déposée par {complainant.get_full_name()}. '
                                f'Employeur : {patron.user.get_full_name()}. '
                                f'Objet : {subject}.',
                    employer_name=patron.user.get_full_name(),
                    workplace_address=addr,
                    workplace_latitude=lat,
                    workplace_longitude=lng,
                    incident_date=date.today() - timedelta(days=20 + idx * 5),
                    status=status,
                    priority=priority,
                    assigned_to=inspector if status != 'PENDING' else None,
                ),
            )
            created_complaints.append(c)
            self.stdout.write(
                f'  {"créée" if created else "existante"} → {number} [{status}] '
                f'{complainant.get_full_name()} → insp. {inspector.get_full_name()}'
            )
        return created_complaints

    # ──────────────────────────────────────────────────────────────────────────
    # PLAINTES VOCALES (EMPLOYE_MAISON)
    # ──────────────────────────────────────────────────────────────────────────
    def _create_voice_complaints(self, workers, inspectors):
        from domestic.models import VoiceComplaint
        self.stdout.write('\n[Plaintes vocales (EMPLOYE_MAISON)]')
        for idx, (wname, ename, lang, commune, lat, lng, status) in enumerate(VOICE_COMPLAINT_DATA):
            worker  = workers[idx % len(workers)]
            insp    = worker.assigned_inspector or inspectors[idx % len(inspectors)]
            # Vérifier si une plainte vocale existe déjà pour ce worker avec ce statut
            existing = VoiceComplaint.objects.filter(
                worker=worker, detected_language=lang
            ).first()
            if existing:
                self.stdout.write(f'  existante → {worker.user.get_full_name()} [{lang}]')
                continue
            VoiceComplaint.objects.create(
                worker=worker,
                audio_file=f'voice_complaints/audio/seed_{idx + 1:02d}_{lang.lower()}.mp3',
                duration_seconds=45 + idx * 15,
                detected_language=lang,
                selected_language=lang,
                language_confidence=0.85 + idx * 0.02,
                commune=commune,
                latitude=float(lat),
                longitude=float(lng),
                status=status,
                assigned_inspector=insp if status not in ('PENDING',) else None,
                transcription_status='PENDING',
                language_assistance_requested=(status == 'ASSISTANCE_REQUESTED'),
                inspector_response_text=(
                    f'Dossier pris en charge. Convocation du patron {ename} programmée.'
                    if status == 'IN_PROGRESS' else ''
                ),
            )
            self.stdout.write(
                f'  créée → {worker.user.get_full_name()} [{lang}] [{status}] '
                f'→ insp. {insp.get_full_name()}'
            )

    # ──────────────────────────────────────────────────────────────────────────
    # PLANNING D'INSPECTION (InspectionRecord)
    # ──────────────────────────────────────────────────────────────────────────
    def _create_inspection_planning(self, enterprises, inspectors):
        from inspections.models import InspectionRecord
        self.stdout.write('\n[Planning inspections (InspectionRecord)]')
        for idx, (ent_i, insp_i, itype, delta_days, completed, result, findings) in enumerate(INSPECTION_PLANNING):
            enterprise = enterprises[ent_i % len(enterprises)]
            inspector  = inspectors[insp_i % len(inspectors)]
            sched_dt   = NOW + timedelta(days=delta_days)
            actual_dt  = sched_dt if completed else None

            existing = InspectionRecord.objects.filter(
                enterprise=enterprise, inspector=inspector,
                inspection_type=itype,
                scheduled_date__date=sched_dt.date(),
            ).first()
            if existing:
                self.stdout.write(f'  existant → {enterprise.name} [{itype}]')
                continue

            InspectionRecord.objects.create(
                enterprise=enterprise,
                inspector=inspector,
                inspection_type=itype,
                scheduled_date=sched_dt,
                actual_date=actual_dt,
                location=enterprise.headquarters_address,
                latitude=enterprise.latitude,
                longitude=enterprise.longitude,
                findings=findings,
                recommendations=(
                    'Mise en conformité sous 30 jours. Visite de contrôle prévue.'
                    if completed and result != 'COMPLIANT' else ''
                ),
                result=result,
                is_completed=completed,
            )
            state = 'terminée' if completed else 'programmée'
            self.stdout.write(
                f'  créée → {enterprise.name} [{itype}] {state} '
                f'→ insp. {inspector.get_full_name()}'
            )

    # ──────────────────────────────────────────────────────────────────────────
    # MÉDIATIONS
    # ──────────────────────────────────────────────────────────────────────────
    def _create_mediations(self, all_complaints, inspectors):
        from mediations.models import Mediation, MediationParticipant
        self.stdout.write('\n[Médiations]')
        # Sélectionner les plaintes en MEDIATION
        mediation_complaints = [c for c in all_complaints if c.status == 'MEDIATION']
        if not mediation_complaints:
            self.stdout.write('  Aucune plainte en statut MEDIATION trouvée.')
            return

        session_types = ['PRESENTIAL', 'ONLINE', 'HYBRID']
        outcomes      = ['PENDING', 'PARTIAL_AGREEMENT', 'AGREEMENT']

        for idx, complaint in enumerate(mediation_complaints[:3]):
            mediator = inspectors[idx % len(inspectors)]
            existing = Mediation.objects.filter(complaint=complaint).first()
            if existing:
                self.stdout.write(f'  existante → {complaint.complaint_number}')
                continue

            stype   = session_types[idx % len(session_types)]
            outcome = outcomes[idx % len(outcomes)]
            sdate   = NOW + timedelta(days=5 + idx * 7)
            med = Mediation.objects.create(
                complaint=complaint,
                mediator=mediator,
                session_date=sdate,
                session_type=stype,
                status='SCHEDULED',
                location=(
                    f'Bureau de l\'inspection du travail — {mediator.inspectorprofile.inspection_zone.city}'
                    if stype != 'ONLINE' else ''
                ),
                meeting_link='https://meet.inspection.ci/mediation' if stype != 'PRESENTIAL' else '',
                outcome=outcome,
            )
            # Ajouter les participants (plaignant + représentant employeur)
            MediationParticipant.objects.get_or_create(
                mediation=med, participant=complaint.complainant,
                defaults=dict(role='EMPLOYEE', name=complaint.complainant.get_full_name()),
            )
            if complaint.assigned_to:
                MediationParticipant.objects.get_or_create(
                    mediation=med, participant=complaint.assigned_to,
                    defaults=dict(role='REPRESENTATIVE', name=complaint.assigned_to.get_full_name()),
                )
            self.stdout.write(
                f'  créée → {complaint.complaint_number} [{stype}] '
                f'médiateur: {mediator.get_full_name()}'
            )

    # ──────────────────────────────────────────────────────────────────────────
    # PROCÉDURES JUDICIAIRES
    # ──────────────────────────────────────────────────────────────────────────
    def _create_judicial_procedures(self, complaints, inspectors):
        from judicial.models import JudicialProcedure
        self.stdout.write('\n[Procédures judiciaires]')
        judicial_complaints = [c for c in complaints if c.status in ('ESCALATED', 'JUDICIAL')]
        if not judicial_complaints:
            self.stdout.write('  Aucune plainte ESCALATED/JUDICIAL trouvée.')
            return

        proc_types = ['UNPAID_WAGES', 'WRONGFUL_TERMINATION', 'HARASSMENT', 'WORKPLACE_ACCIDENT']
        courts     = [
            'Tribunal du Travail d\'Abidjan',
            'Tribunal du Travail de Bouaké',
            'Tribunal du Travail de Daloa',
        ]

        for idx, complaint in enumerate(judicial_complaints[:2]):
            officer = inspectors[idx % len(inspectors)]
            if JudicialProcedure.objects.filter(complaint=complaint).exists():
                self.stdout.write(f'  existante → {complaint.complaint_number}')
                continue

            ptype  = proc_types[idx % len(proc_types)]
            court  = courts[idx % len(courts)]
            amount = 500000 + idx * 250000

            JudicialProcedure.objects.create(
                complaint=complaint,
                procedure_type=ptype,
                status='SUBMITTED',
                plaintiff=complaint.complainant,
                defendant_name=complaint.employer_name or 'Employeur inconnu',
                court_name=court,
                filed_date=date.today() - timedelta(days=10 + idx * 5),
                submission_date=date.today() - timedelta(days=5 + idx * 3),
                case_officer=officer,
                summary=(
                    f'Procédure judiciaire initiée suite à la plainte {complaint.complaint_number}. '
                    f'Faits : {complaint.subject}. '
                    f'Plaignant(e) : {complaint.complainant.get_full_name()}. '
                    f'Défendeur : {complaint.employer_name}.'
                ),
                legal_grounds=(
                    'Art. 14 et 17 du Code du Travail ivoirien. '
                    'Décret n°96-204 du 7 mars 1996 relatif aux salaires. '
                    'Convention collective interprofessionnelle.'
                ),
                claims=(
                    f'Paiement des arriérés de salaire. '
                    f'Dommages et intérêts pour préjudice subi. '
                    f'Montant réclamé : {amount:,} FCFA.'
                ),
                claimed_amount=amount,
            )
            self.stdout.write(
                f'  créée → {complaint.complaint_number} [{ptype}] '
                f'tribunal: {court} → officier: {officer.get_full_name()}'
            )

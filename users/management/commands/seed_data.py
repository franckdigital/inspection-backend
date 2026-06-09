"""
python manage.py seed_data

Creates demo data:
  - 5 InspectionZones (one per local language region)
  - 10 Inspectors (2 per zone, each zone linked to a local language)
  - 5 Enterprises with full info
  - 5 Enterprise employees (EMPLOYE) assigned to enterprises
  - 5 Domestic employers / patrons (EMPLOYEUR) with DomesticEmployer profile
  - 5 Domestic workers (EMPLOYE_MAISON) with DomesticWorker profile + DomesticContract
"""

from datetime import date, time
from django.core.management.base import BaseCommand
from django.db import transaction


LANGUAGES = [
    ('DIOULA',   'Dioula',   'Bouaké',       'Vallée du Bandama', '7.69', '-5.03'),
    ('BAOULE',   'Baoulé',   'Yamoussoukro', 'Lacs',              '6.82', '-5.27'),
    ('BETE',     'Bété',     'Daloa',         'Haut-Sassandra',    '6.87', '-6.45'),
    ('SENOUFO',  'Sénoufo',  'Korhogo',      'Poro',              '9.46', '-5.63'),
    ('ANYIN',    'Anyin',    'Abengourou',   'Indénié-Djuablin',  '6.73', '-3.49'),
]

INSPECTOR_NAMES = [
    ('Mamadou',   'Coulibaly'), ('Ibrahim',   'Traoré'),    # Dioula
    ('Kouassi',   'Konan'),     ('Akissi',    'Assoumou'),  # Baoulé
    ('Gnagno',    'Gbagbo'),    ('Séraphin',  'Daho'),      # Bété
    ('Navigué',   'Silué'),     ('Dramane',   'Koné'),      # Sénoufo
    ('Adjoua',    'Assi'),      ('Konan',     'Attia'),     # Anyin
]

ENTERPRISE_DATA = [
    {
        'name': 'SIVOCI Industrie SA',
        'legal_form': 'SA',
        'rccm': 'CI-ABJ-2018-B-04521',
        'nif': 'CI-2018-00041',
        'sector': 'INDUSTRIE',
        'headquarters_address': 'Zone Industrielle de Yopougon, Lot 47',
        'city': 'Abidjan',
        'region': 'Lagunes',
        'phone': '+2252722345001',
        'email': 'contact@sivoci.ci',
        'employee_count': 210,
        'founding_date': date(2018, 3, 15),
        'lat': '5.3600', 'lng': '-4.0083',
    },
    {
        'name': 'Groupe Agro-CI SARL',
        'legal_form': 'SARL',
        'rccm': 'CI-ABJ-2015-B-01873',
        'nif': 'CI-2015-00082',
        'sector': 'AGRICULTURE',
        'headquarters_address': '12 Rue des Cacaoyères, Plateau',
        'city': 'Abidjan',
        'region': 'Lagunes',
        'phone': '+2252722345002',
        'email': 'info@agroci.ci',
        'employee_count': 85,
        'founding_date': date(2015, 7, 20),
        'lat': '5.3197', 'lng': '-4.0167',
    },
    {
        'name': 'TechPrime Côte d\'Ivoire SAS',
        'legal_form': 'SAS',
        'rccm': 'CI-ABJ-2020-B-07732',
        'nif': 'CI-2020-00153',
        'sector': 'TECHNOLOGIE',
        'headquarters_address': 'Immeuble Star 3, Avenue Lamblin',
        'city': 'Abidjan',
        'region': 'Lagunes',
        'phone': '+2252722345003',
        'email': 'hello@techprime.ci',
        'employee_count': 47,
        'founding_date': date(2020, 1, 8),
        'lat': '5.3215', 'lng': '-4.0183',
    },
    {
        'name': 'Hôtel Savane Palace',
        'legal_form': 'SARL',
        'rccm': 'CI-BKE-2012-B-00334',
        'nif': 'CI-2012-00217',
        'sector': 'HOTELLERIE',
        'headquarters_address': 'Avenue de la République, Quartier Commerce',
        'city': 'Bouaké',
        'region': 'Vallée du Bandama',
        'phone': '+2252722345004',
        'email': 'reservation@savaneci.ci',
        'employee_count': 130,
        'founding_date': date(2012, 11, 1),
        'lat': '7.6833', 'lng': '-5.0333',
    },
    {
        'name': 'BTP Construction Daloa',
        'legal_form': 'EI',
        'rccm': 'CI-DAL-2017-B-00891',
        'nif': 'CI-2017-00398',
        'sector': 'CONSTRUCTION',
        'headquarters_address': 'Route de Vavoua, km 4',
        'city': 'Daloa',
        'region': 'Haut-Sassandra',
        'phone': '+2252722345005',
        'email': 'direction@btpdaloa.ci',
        'employee_count': 65,
        'founding_date': date(2017, 5, 14),
        'lat': '6.8770', 'lng': '-6.4502',
    },
]

EMPLOYEE_DATA = [
    ('Fofana',   'Lassina',  'M', '1990-04-12', 'Technicien de production',   '2021-03-01', 'Abidjan', '225060100001'),
    ('Ouédraogo','Awa',      'F', '1994-08-25', 'Responsable qualité',        '2020-07-15', 'Abidjan', '225060100002'),
    ('N\'Goran', 'Serge',    'M', '1988-12-05', 'Agronome terrain',           '2019-01-10', 'Abidjan', '225060100003'),
    ('Koffi',    'Amenan',   'F', '1996-02-18', 'Développeur fullstack',      '2022-06-01', 'Abidjan', '225060100004'),
    ('Ouattara', 'Issouf',   'M', '1985-09-30', 'Chef de chantier',           '2018-11-20', 'Bouaké',  '225060100005'),
]

PATRON_DATA = [
    ('Diabaté',  'Fatoumata', 'F', '1975-03-10', 'Cocody, Rue des Jardins 14',        'Abidjan',  '5.3600', '-3.9900', '225070200001'),
    ('Bamba',    'Drissa',    'M', '1968-07-22', 'Marcory, Rue du Commerce 7',        'Abidjan',  '5.2900', '-4.0000', '225070200002'),
    ('Ettien',   'Clarisse',  'F', '1980-11-05', 'Plateau, Avenue Chardy 3',          'Abidjan',  '5.3197', '-4.0167', '225070200003'),
    ('Coulibaly','Adama',     'M', '1972-01-30', 'Quartier Kôkô, Résidence Forêt 2', 'Korhogo',  '9.4590', '-5.6290', '225070200004'),
    ('Konan',    'Evelyne',   'F', '1983-06-14', 'Quartier Air France, Villa 8',      'Bouaké',   '7.6880', '-5.0210', '225070200005'),
]

WORKER_DATA = [
    ('Sanogo',   'Aminata',  'F', '2000-05-20', 'HOUSEKEEPER', 3, 'Abobo, Cité Belle Vie', 'Abidjan',  '225080300001'),
    ('Traoré',   'Mariam',   'F', '1998-09-08', 'COOK',        5, 'Yopougon, Quartier Kennedy', 'Abidjan', '225080300002'),
    ('Bah',      'Mamou',    'F', '2002-01-15', 'NANNY',       2, 'Treichville, Rue 10', 'Abidjan',  '225080300003'),
    ('Bakayoko', 'Seydou',   'M', '1997-04-03', 'GARDENER',    4, 'Quartier Kôkô Sud',   'Korhogo',  '225080300004'),
    ('Yao',      'Akissi',   'F', '2001-11-28', 'GENERAL',     1, 'Quartier Air France', 'Bouaké',   '225080300005'),
]


class Command(BaseCommand):
    help = 'Seed demo data for inspectors, enterprises, domestic workers, and patrons'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')
        try:
            with transaction.atomic():
                zones = self._create_zones()
                self._create_inspectors(zones)
                enterprises = self._create_enterprises()
                self._create_enterprise_employees(enterprises)
                patrons = self._create_domestic_patrons()
                self._create_domestic_workers(patrons)
            self.stdout.write(self.style.SUCCESS('Seed completed successfully.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Seed failed: {e}'))
            raise

    # ------------------------------------------------------------------
    def _create_zones(self):
        from inspections.models import InspectionZone
        zones = {}
        for lang_code, lang_label, city, region, lat, lng in LANGUAGES:
            zone, created = InspectionZone.objects.get_or_create(
                code=f'ZONE-{lang_code}',
                defaults=dict(
                    name=f'Zone Inspection — {lang_label}',
                    region=region,
                    city=city,
                    description=f'Zone desservant les communautés de langue {lang_label}',
                    latitude=lat,
                    longitude=lng,
                    is_active=True,
                ),
            )
            zones[lang_code] = zone
            status = 'créée' if created else 'déjà existante'
            self.stdout.write(f'  Zone {zone.code} {status}')
        return zones

    # ------------------------------------------------------------------
    def _create_inspectors(self, zones):
        from users.models import User, InspectorProfile
        lang_keys = list(zones.keys())
        for idx, (last_name, first_name) in enumerate(INSPECTOR_NAMES):
            lang_code = lang_keys[idx // 2]
            lang_label = LANGUAGES[idx // 2][1]
            email = f'inspecteur.{first_name.lower()}.{last_name.lower()}@inspection.ci'
            phone = f'+2250100{10 + idx:04d}'
            user, created = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first_name,
                    last_name=last_name,
                    user_type='INSPECTEUR',
                    phone_number=phone,
                    gender='M' if idx % 3 != 1 else 'F',
                    is_active=True,
                    is_verified=True,
                ),
            )
            if created:
                user.set_password('Inspect@2024!')
                user.save()
            InspectorProfile.objects.get_or_create(
                user=user,
                defaults=dict(
                    badge_number=f'INSP-CI-{2024}-{idx + 1:03d}',
                    inspection_zone=zones[lang_code],
                    specialization=f'Langue locale: {lang_label} — Droit du travail',
                ),
            )
            status = 'créé' if created else 'déjà existant'
            self.stdout.write(f'  Inspecteur {user.get_full_name()} ({lang_label}) {status}')

    # ------------------------------------------------------------------
    def _create_enterprises(self):
        from enterprises.models import Enterprise
        enterprises = []
        for d in ENTERPRISE_DATA:
            ent, created = Enterprise.objects.get_or_create(
                rccm=d['rccm'],
                defaults=dict(
                    name=d['name'],
                    legal_form=d['legal_form'],
                    nif=d['nif'],
                    sector=d['sector'],
                    headquarters_address=d['headquarters_address'],
                    city=d['city'],
                    region=d['region'],
                    country='CI',
                    phone_number=d['phone'],
                    email=d['email'],
                    employee_count=d['employee_count'],
                    founding_date=d['founding_date'],
                    latitude=d['lat'],
                    longitude=d['lng'],
                    compliance_score=70,
                    risk_level='LOW',
                    is_active=True,
                    is_verified=True,
                ),
            )
            enterprises.append(ent)
            status = 'créée' if created else 'déjà existante'
            self.stdout.write(f'  Entreprise {ent.name} {status}')
        return enterprises

    # ------------------------------------------------------------------
    def _create_enterprise_employees(self, enterprises):
        from users.models import User, EmployeeProfile
        for idx, (last, first, gender, dob, title, hire, city, phone_sfx) in enumerate(EMPLOYEE_DATA):
            email = f'employe.{first.lower()}.{last.lower().replace("\'", "")}@work.ci'
            phone = f'+{phone_sfx}'
            user, created = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first,
                    last_name=last,
                    user_type='EMPLOYE',
                    phone_number=phone,
                    gender=gender,
                    date_of_birth=date.fromisoformat(dob),
                    is_active=True,
                    is_verified=True,
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
                    city=city,
                    job_title=title,
                    hire_date=date.fromisoformat(hire),
                    current_employer=enterprise,
                ),
            )
            status = 'créé' if created else 'déjà existant'
            self.stdout.write(f'  Salarié {user.get_full_name()} → {enterprise.name} {status}')

    # ------------------------------------------------------------------
    def _create_domestic_patrons(self):
        from users.models import User
        from domestic.models import DomesticEmployer
        patrons = []
        for idx, (last, first, gender, dob, address, city, lat, lng, phone_sfx) in enumerate(PATRON_DATA):
            email = f'patron.{first.lower()}.{last.lower()}@famille.ci'
            phone = f'+{phone_sfx}'
            user, created = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first,
                    last_name=last,
                    user_type='EMPLOYEUR',
                    phone_number=phone,
                    gender=gender,
                    date_of_birth=date.fromisoformat(dob),
                    is_active=True,
                    is_verified=True,
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
                    address=address,
                    city=city,
                    latitude=lat,
                    longitude=lng,
                ),
            )
            patrons.append(employer)
            status = 'créé' if created else 'déjà existant'
            self.stdout.write(f'  Patron {user.get_full_name()} ({city}) {status}')
        return patrons

    # ------------------------------------------------------------------
    def _create_domestic_workers(self, patrons):
        from users.models import User
        from domestic.models import DomesticWorker, DomesticContract
        for idx, (last, first, gender, dob, spec, exp, address, city, phone_sfx) in enumerate(WORKER_DATA):
            email = f'employe.maison.{first.lower()}.{last.lower()}@travail.ci'
            phone = f'+{phone_sfx}'
            user, created = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first,
                    last_name=last,
                    user_type='EMPLOYE_MAISON',
                    phone_number=phone,
                    gender=gender,
                    date_of_birth=date.fromisoformat(dob),
                    is_active=True,
                    is_verified=True,
                ),
            )
            if created:
                user.set_password('Worker@2024!')
                user.save()
            patron = patrons[idx % len(patrons)]
            worker, _ = DomesticWorker.objects.get_or_create(
                user=user,
                defaults=dict(
                    specialization=spec,
                    years_experience=exp,
                    is_available=False,
                    preferred_work_days=['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi'],
                ),
            )
            DomesticContract.objects.get_or_create(
                worker=worker,
                employer=patron,
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
            status = 'créé' if created else 'déjà existant'
            self.stdout.write(
                f'  Employé maison {user.get_full_name()} → patron {patron.user.get_full_name()} {status}'
            )

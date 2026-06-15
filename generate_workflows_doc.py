"""
Génère le document Word de documentation des workflows de la
Plateforme Nationale e-Inspection du Travail — Côte d'Ivoire
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import date

# ── Couleurs CI ──────────────────────────────────────────────────────────────
ORANGE  = RGBColor(0xF4, 0x7E, 0x1C)   # Drapeau CI
VERT    = RGBColor(0x00, 0x9A, 0x44)   # Drapeau CI
ROUGE   = RGBColor(0xDC, 0x26, 0x26)
BLEU    = RGBColor(0x1D, 0x4E, 0xD8)
GRIS    = RGBColor(0x6B, 0x72, 0x80)
GRIS_BG = RGBColor(0xF3, 0xF4, 0xF6)
BLANC   = RGBColor(0xFF, 0xFF, 0xFF)
NOIR    = RGBColor(0x11, 0x18, 0x27)

doc = Document()

# ── Marges ───────────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.0)


# ── Helpers ──────────────────────────────────────────────────────────────────
def set_cell_bg(cell, hex_color: str):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  hex_color)
    tcPr.append(shd)


def set_cell_borders(cell, color='DDDDDD'):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for side in ('top', 'left', 'bottom', 'right'):
        b = OxmlElement(f'w:{side}')
        b.set(qn('w:val'),   'single')
        b.set(qn('w:sz'),    '4')
        b.set(qn('w:space'), '0')
        b.set(qn('w:color'), color)
        tcBorders.append(b)
    tcPr.append(tcBorders)


def heading1(text, color=ORANGE):
    p = doc.add_paragraph()
    p.clear()
    run = p.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = color
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(6)
    # Ligne de séparation
    border = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'),   'single')
    bottom.set(qn('w:sz'),    '8')
    bottom.set(qn('w:space'), '2')
    bottom.set(qn('w:color'), 'F47E1C')
    border.append(bottom)
    p._p.get_or_add_pPr().append(border)
    return p


def heading2(text, color=BLEU):
    p = doc.add_paragraph()
    p.clear()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(13)
    run.font.color.rgb = color
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(4)
    return p


def heading3(text):
    p = doc.add_paragraph()
    p.clear()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = NOIR
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(3)
    return p


def body(text, italic=False, color=None):
    p = doc.add_paragraph()
    p.clear()
    run = p.add_run(text)
    run.font.size   = Pt(10.5)
    run.italic      = italic
    if color:
        run.font.color.rgb = color
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.space_before = Pt(0)
    return p


def bullet(text, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.clear()
    run = p.add_run(('    ' * level) + '• ' + text)
    run.font.size = Pt(10.5)
    p.paragraph_format.space_after  = Pt(2)
    p.paragraph_format.space_before = Pt(0)
    return p


def numbered(text, level=0):
    p = doc.add_paragraph()
    p.clear()
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    p.paragraph_format.left_indent  = Cm(0.5 * (level + 1))
    p.paragraph_format.space_after  = Pt(2)
    return p


def status_table(headers, rows, header_bg='009A44'):
    """Table générique stylisée."""
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    # En-tête
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        set_cell_bg(cell, header_bg)
        p = cell.paragraphs[0]
        p.clear()
        run = p.add_run(h)
        run.bold = True
        run.font.size = Pt(9.5)
        run.font.color.rgb = BLANC
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Données
    for ri, row_data in enumerate(rows):
        bg = 'F9FAFB' if ri % 2 == 0 else 'FFFFFF'
        for ci, val in enumerate(row_data):
            cell = t.rows[ri + 1].cells[ci]
            set_cell_bg(cell, bg)
            set_cell_borders(cell, 'E5E7EB')
            p = cell.paragraphs[0]
            p.clear()
            run = p.add_run(str(val))
            run.font.size = Pt(9.5)
    doc.add_paragraph()  # espacement
    return t


def flow_table(steps, color='009A44'):
    """Table de workflow en colonnes avec flèches."""
    t = doc.add_table(rows=2, cols=len(steps))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (label, desc) in enumerate(steps):
        c1 = t.rows[0].cells[i]
        set_cell_bg(c1, color)
        p = c1.paragraphs[0]
        p.clear()
        run = p.add_run(label)
        run.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = BLANC
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        c2 = t.rows[1].cells[i]
        set_cell_bg(c2, 'F0FDF4')
        p = c2.paragraphs[0]
        p.clear()
        run = p.add_run(desc)
        run.font.size = Pt(8.5)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()
    return t


# ════════════════════════════════════════════════════════════════════════════
#  PAGE DE COUVERTURE
# ════════════════════════════════════════════════════════════════════════════
p = doc.add_paragraph()
p.clear()
run = p.add_run('DOCUMENTATION DES WORKFLOWS')
run.bold = True
run.font.size = Pt(28)
run.font.color.rgb = ORANGE
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(60)

p = doc.add_paragraph()
p.clear()
run = p.add_run('Plateforme Nationale e-Inspection du Travail')
run.bold = True
run.font.size = Pt(18)
run.font.color.rgb = VERT
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph()
p = doc.add_paragraph()
p.clear()
run = p.add_run('Ministère de l\'Emploi et de la Protection Sociale')
run.font.size = Pt(13)
run.font.color.rgb = GRIS
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

p = doc.add_paragraph()
p.clear()
run = p.add_run('République de Côte d\'Ivoire')
run.font.size = Pt(12)
run.italic = True
run.font.color.rgb = GRIS
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph()
doc.add_paragraph()

meta = [
    ('Référence',   'DOC-WF-EINSP-CI-2026-001'),
    ('Version',     '1.0'),
    ('Date',        date.today().strftime('%d %B %Y')),
    ('Statut',      'Validé'),
    ('Auteur',      'Direction Générale du Travail'),
    ('Diffusion',   'Confidentiel — Usage interne'),
]
t = doc.add_table(rows=len(meta), cols=2)
t.style = 'Table Grid'
t.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, (k, v) in enumerate(meta):
    bg = 'F47E1C' if i == 0 else ('F9FAFB' if i % 2 == 0 else 'FFFFFF')
    c0 = t.rows[i].cells[0]
    c1 = t.rows[i].cells[1]
    set_cell_bg(c0, bg)
    set_cell_bg(c1, 'FFFFFF' if i > 0 else 'FFF7ED')
    p0 = c0.paragraphs[0]
    p0.clear()
    r0 = p0.add_run(k)
    r0.bold = True
    r0.font.size = Pt(10)
    r0.font.color.rgb = BLANC if i == 0 else NOIR
    p1 = c1.paragraphs[0]
    p1.clear()
    r1 = p1.add_run(v)
    r1.font.size = Pt(10)

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  SOMMAIRE
# ════════════════════════════════════════════════════════════════════════════
heading1('Sommaire')

toc = [
    ('1.',  'Contexte et périmètre'),
    ('2.',  'Architecture technique'),
    ('3.',  'Rôles et permissions (RBAC)'),
    ('4.',  'Workflow des Plaintes'),
    ('5.',  'Workflow de Médiation / Conciliation'),
    ('6.',  'Workflow de Convocation — Accusé de réception'),
    ('7.',  'Gestion des Non-Comparutions (Employeur absent)'),
    ('8.',  'Workflow des Accords'),
    ('9.',  'Procédures Judiciaires et Escalade'),
    ('10.', 'Tâches Celery automatiques'),
    ('11.', 'Référentiel des endpoints API'),
    ('12.', 'Notifications multi-canal'),
    ('13.', 'Sécurité et conformité'),
]
for num, title in toc:
    p = doc.add_paragraph()
    p.clear()
    run = p.add_run(f'{num.ljust(5)}{title}')
    run.font.size = Pt(11)
    p.paragraph_format.space_after  = Pt(3)
    p.paragraph_format.left_indent  = Cm(0.5)

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  1. CONTEXTE ET PÉRIMÈTRE
# ════════════════════════════════════════════════════════════════════════════
heading1('1. Contexte et périmètre')

body(
    'La Plateforme Nationale e-Inspection du Travail est un système d\'information '
    'déployé par la Direction Générale du Travail (DGT) du Ministère de l\'Emploi '
    'et de la Protection Sociale de Côte d\'Ivoire. Elle couvre l\'ensemble du cycle '
    'de vie du traitement des plaintes de travailleurs, de la médiation à la résolution '
    'judiciaire, en conformité avec le Code du Travail ivoirien (Loi n° 2015-532 du 20 juillet 2015).'
)

heading2('Périmètre fonctionnel')
for item in [
    'Dépôt et traitement des plaintes de travailleurs',
    'Planification et conduite des séances de médiation/conciliation',
    'Convocation multi-canal des parties (email, SMS, notification mobile)',
    'Accusé de réception traçable avec jeton UUID',
    'Gestion des non-comparutions avec génération de PV de carence',
    'Rédaction et signature électronique des accords',
    'Escalade hiérarchique et procédures judiciaires',
    'Tableau de bord et indicateurs de performance',
]:
    bullet(item)

heading2('Cadre légal')
body('Code du Travail — Loi n° 2015-532 du 20 juillet 2015 (JOCI n° 32 du 09/08/2016)')
body('Règlement n° 05/2002/CM/UEMOA sur la libre circulation des travailleurs')
body('Loi n° 2013-450 du 19 juin 2013 relative à la protection des données à caractère personnel')

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  2. ARCHITECTURE TECHNIQUE
# ════════════════════════════════════════════════════════════════════════════
heading1('2. Architecture technique')

status_table(
    ['Couche', 'Technologie', 'Version', 'Rôle'],
    [
        ['Backend API',      'Django + DRF',         '5.0.6 / 3.15.1',  'API REST, logique métier, authentification'],
        ['Base de données',  'MySQL / MariaDB',       '8.0+',            'Persistance des données'],
        ['Authentification', 'SimpleJWT + OTP/2FA',   '5.3.1',           'JWT access/refresh + 2FA'],
        ['Tâches async',     'Celery + Redis',         '5.3.6',           'Envoi emails/SMS, tâches planifiées'],
        ['WebSocket',        'Django Channels',        '4.1.0',           'Notifications temps réel'],
        ['Frontend web',     'React + TypeScript',     '18+',             'Interface inspecteurs & employeurs'],
        ['Mobile',           'React Native / Expo',    '50+',             'Application iOS et Android'],
        ['Documents Word',   'python-docx',            '1.2.0',           'Génération PV, accords, offres'],
        ['Email',            'Django SMTP',            '-',               'Convocations, alertes, relances'],
        ['SMS',              'Orange CI / MTN CI',     '-',               'Convocations SMS (+225)'],
        ['Timezone',         'Africa/Abidjan',         'UTC+0',           'Fuseau horaire Côte d\'Ivoire'],
    ],
    header_bg='F47E1C',
)

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  3. RÔLES ET PERMISSIONS (RBAC)
# ════════════════════════════════════════════════════════════════════════════
heading1('3. Rôles et permissions (RBAC)')

body('Le système implémente un contrôle d\'accès basé sur les rôles (RBAC) avec 8 profils :')

status_table(
    ['Rôle', 'Code', 'Périmètre', 'Accès Médiation'],
    [
        ['Travailleur (salarié)',           'EMPLOYE',           'Ses propres plaintes',             'Lecture séances le concernant'],
        ['Travailleur domestique',          'EMPLOYE_MAISON',    'Ses propres plaintes',             'Lecture séances le concernant'],
        ['Employeur',                       'EMPLOYEUR',         'Son entreprise',                   'Espace convocation, accusé réception'],
        ['Inspecteur du Travail',           'INSPECTEUR',        'Plaintes assignées',               'CRUD séances, convocation, PV carence'],
        ['Chef d\'inspection',              'CHEF_INSPECTION',   'Son inspection',                   'Supervision, escalade'],
        ['Directeur Régional',              'DIRECTEUR_REGIONAL','Sa région',                        'Tableau de bord régional'],
        ['Directeur Général',               'DIRECTEUR_GENERAL', 'National',                         'Vue globale, validation'],
        ['Administrateur système',          'ADMIN',             'Tout le système',                  'Accès total'],
    ],
    header_bg='009A44',
)

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  4. WORKFLOW DES PLAINTES
# ════════════════════════════════════════════════════════════════════════════
heading1('4. Workflow des Plaintes')

heading2('4.1 Diagramme de statuts')
flow_table([
    ('PENDING\n(En attente)', 'Plainte déposée\nnon encore traitée'),
    ('ASSIGNED\n(Assignée)',  'Inspecteur\nattribué'),
    ('IN_PROGRESS\n(En cours)', 'Enquête\nen cours'),
    ('UNDER_INVESTIGATION\n(Investigation)', 'Instruction\napprofondie'),
    ('MEDIATION\n(Médiation)',  'Séance de\nmédiation planifiée'),
    ('RESOLVED\n(Résolue)',    'Clôturée\namiablement'),
], color='1D4ED8')

heading2('4.2 Statuts de sortie alternatifs')
status_table(
    ['Statut', 'Code', 'Déclencheur', 'Action suivante'],
    [
        ['Résolu judiciaire',   'JUDICIAL',   'Médiation échouée ou accord rompu',   'Procédure Tribunal du Travail'],
        ['Escaladé',            'ESCALATED',  'Non-comparution employeur × 3',       'Transmission hiérarchie'],
        ['Classé sans suite',   'CLOSED',     'Désistement du plaignant',            'Archivage'],
    ],
    header_bg='DC2626',
)

heading2('4.3 Processus de dépôt')
for n, step in enumerate([
    '1. Le travailleur se connecte et remplit le formulaire de plainte (mobile ou web).',
    '2. La plainte reçoit le statut PENDING et un numéro de référence unique.',
    '3. Le Chef d\'Inspection assigne la plainte à un inspecteur disponible → statut ASSIGNED.',
    '4. L\'inspecteur instruit le dossier, change le statut en IN_PROGRESS.',
    '5. Si la complexité le requiert, il passe en UNDER_INVESTIGATION.',
    '6. L\'inspecteur propose une médiation → statut MEDIATION + création de la séance.',
    '7. À l\'issue de la médiation : RESOLVED (accord signé) ou JUDICIAL (échec).',
], 1):
    bullet(step)

heading2('4.4 Notifications automatiques')
bullet('Dépôt plainte → email de confirmation au travailleur')
bullet('Assignation → email à l\'inspecteur avec récapitulatif du dossier')
bullet('Changement de statut → email + push notification au plaignant')
bullet('Médiation planifiée → convocations email+SMS à toutes les parties')

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  5. WORKFLOW MÉDIATION / CONCILIATION
# ════════════════════════════════════════════════════════════════════════════
heading1('5. Workflow de Médiation / Conciliation')

heading2('5.1 Distinction Médiation / Conciliation')
body(
    'Dans le système, les termes "Médiation" et "Conciliation" désignent le même '
    'processus de résolution amiable. Le médiateur est un Inspecteur ou Chef d\'Inspection '
    'qui facilite le dialogue entre le travailleur et l\'employeur. La conciliation est '
    'la phase préalable obligatoire avant tout recours judiciaire (Art. 81 du Code du Travail).'
)

heading2('5.2 Cycle de vie d\'une séance')
flow_table([
    ('SCHEDULED\n(Planifiée)',   'Séance créée,\nconvocations envoyées'),
    ('ONGOING\n(En cours)',      'Séance démarrée\npar le médiateur'),
    ('COMPLETED\n(Terminée)',    'Séance close\navec ou sans accord'),
    ('POSTPONED\n(Reportée)',    'Renvoi à une\nnouvelle date'),
    ('CANCELLED\n(Annulée)',     'Annulation\ndéfinitive'),
], color='009A44')

heading2('5.3 Création d\'une séance de médiation')
for step in [
    '1. L\'inspecteur crée une séance via POST /mediations/sessions/ en liant la plainte concernée.',
    '2. Il définit la date, l\'heure, le lieu (présentiel/visio/hybride) et désigne le médiateur.',
    '3. Il ajoute les participants : travailleur plaignant, employeur (rôles EMPLOYEE/EMPLOYER).',
    '4. Il déclenche les convocations via POST /mediations/sessions/{id}/convoke/.',
    '5. Les convocations sont envoyées simultanément par email, SMS et notification push.',
    '6. Chaque envoi est tracé dans ConvocationAttempt (canal, statut, horodatage, ID fournisseur).',
]:
    bullet(step)

heading2('5.4 Résultats possibles de la séance')
status_table(
    ['Résultat', 'Code', 'Condition', 'Suite'],
    [
        ['Accord trouvé',            'AGREEMENT',         'Toutes parties d\'accord',   'Création + signature de l\'accord'],
        ['Accord partiel',           'PARTIAL_AGREEMENT', 'Accord sur certains points', 'Accord partiel + nouvelle séance possible'],
        ['Pas d\'accord',            'NO_AGREEMENT',      'Désaccord total',            'Renvoi judiciaire → statut JUDICIAL'],
        ['Non-comparution employeur','(voir §7)',          'Employeur absent',           'PV de carence + escalade hiérarchique'],
        ['En attente',               'PENDING',           'Séance non encore tenue',    'En attente de la date de séance'],
    ],
    header_bg='0F766E',
)

heading2('5.5 Rédaction du Procès-Verbal de séance')
for step in [
    '1. Après la séance, l\'inspecteur remplit le PV via POST /mediations/sessions/{id}/generate_minutes/.',
    '2. Le PV contient : déclaration d\'ouverture, déclarations des parties, synthèse des débats, accords atteints.',
    '3. Le PV est signé électroniquement par toutes les parties.',
    '4. Une copie PDF est générée et attachée à la séance (MediationDocument de type MINUTES).',
]:
    bullet(step)

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  6. WORKFLOW CONVOCATION — ACCUSÉ DE RÉCEPTION
# ════════════════════════════════════════════════════════════════════════════
heading1('6. Workflow de Convocation — Accusé de réception')

heading2('6.1 Problème résolu')
body(
    'Un problème récurrent rencontré par les Inspecteurs du Travail est le refus des '
    'employeurs de prendre acte des convocations (refus de signer le courrier, absence '
    'au bureau, téléphone non répondu). Le système implémente une solution multi-canal '
    'traçable qui constitue une preuve légale d\'envoi de la convocation.'
)

heading2('6.2 Mécanisme de convocation traçable')
body('Chaque participant reçoit un jeton UUID unique (acknowledgment_token) stocké en base. Ce jeton est inclus dans les liens email et SMS sous la forme :')
body('    https://e-inspection.ci/convocation/confirmer/{token}/', italic=True, color=BLEU)
body('Lorsque le destinataire clique ce lien, le timestamp acknowledged_at est enregistré sans nécessiter de connexion.')

heading2('6.3 Diagramme de convocation')
flow_table([
    ('Non convoqué',   'Participant\najouté à la séance'),
    ('Convocation\nenvoyée', 'Email + SMS + Push\nenvoyés simultanément'),
    ('Livré',          'Accusé de réception\nélectronique (clic lien)'),
    ('Confirmé\nmanuellement', 'L\'inspecteur confirme\nla réception en présentiel'),
    ('Non-comparution', 'Aucun accusé après\n3 relances → PV carence'),
], color='1D4ED8')

heading2('6.4 Canaux de notification')
status_table(
    ['Canal', 'Code', 'Fournisseur', 'Lien de confirmation', 'Preuve légale'],
    [
        ['Email',               'EMAIL',  'Django SMTP',          'Lien UUID cliquable',  'Oui — timestamp clic'],
        ['SMS',                 'SMS',    'Orange CI / MTN CI / Moov Africa',  'Lien court UUID',      'Oui — timestamp clic'],
        ['Push mobile',         'PUSH',   'Django Channels / Firebase',         'Deep link',            'Oui — timestamp push'],
        ['Confirmation manuelle','MANUAL', 'Inspecteur en présentiel',          'N/A',                  'Oui — inspecteur signataire'],
    ],
    header_bg='7C3AED',
)

heading2('6.5 API de convocation')
status_table(
    ['Action', 'Méthode', 'Endpoint', 'Permission'],
    [
        ['Envoyer convocations',   'POST', '/mediations/sessions/{id}/convoke/',                    'INSPECTEUR+'],
        ['Accuser réception (lien)','GET', '/mediations/sessions/acknowledge/{token}/',             'Public (sans auth)'],
        ['Confirmer manuellement', 'POST', '/mediations/sessions/{id}/manual_acknowledge/',        'INSPECTEUR+'],
        ['Relancer',               'POST', '/mediations/sessions/{id}/relance/',                   'INSPECTEUR+'],
        ['Voir en attente',        'GET',  '/mediations/sessions/pending_acknowledgment/',          'INSPECTEUR+'],
    ],
    header_bg='0F766E',
)

heading2('6.6 Rotation des canaux lors des relances')
body('Pour maximiser les chances d\'atteindre l\'employeur, les relances utilisent une rotation de canaux :')
bullet('Relance n°1 (48h après la 1ère convocation) → EMAIL')
bullet('Relance n°2 (24h après) → SMS')
bullet('Relance n°3 (24h après) → PUSH')
bullet('Au-delà de 3 relances → escalade automatique à la hiérarchie')

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  7. GESTION DES NON-COMPARUTIONS
# ════════════════════════════════════════════════════════════════════════════
heading1('7. Gestion des Non-Comparutions (Employeur absent)')

heading2('7.1 Cadre légal')
body(
    'Conformément au Code du Travail ivoirien (Loi n° 2015-532), le refus de comparaître '
    'devant l\'Inspection du Travail après convocation régulière constitue une infraction '
    'passible de sanctions pécuniaires et peut entraîner l\'engagement de poursuites judiciaires.'
)

heading2('7.2 Processus de constat de non-comparution')
for step in [
    '1. Le jour de la séance, si l\'employeur ne se présente pas, l\'inspecteur attend 30 minutes (délai de tolérance).',
    '2. Il ouvre l\'interface d\'administration ou l\'application mobile.',
    '3. Il clique "Constater la non-comparution" sur la séance concernée.',
    '4. Il remplit le formulaire : notes circonstanciées, cocher "Ouvrir PV d\'infraction" si souhaité, cocher "Escalader à la hiérarchie".',
    '5. Il soumet via POST /mediations/sessions/{id}/report_no_show/.',
    '6. Le système effectue automatiquement les actions ci-dessous.',
]:
    bullet(step)

heading2('7.3 Actions automatiques déclenchées')
status_table(
    ['Action', 'Détail', 'Acteur'],
    [
        ['Enregistrement',        'employer_no_show=True, no_show_reported_at=now, no_show_reported_by=inspecteur',                         'Système'],
        ['Statut plainte',        'Plainte → ESCALATED (ou JUDICIAL si open_infraction_pv)',                                                  'Système'],
        ['Score conformité',      'compliance_score de l\'entreprise − 15 points',                                                            'Système'],
        ['PV de carence',         'Document MediationDocument de type PV_CARENCE généré et attaché à la séance',                             'Système'],
        ['PV d\'infraction',      'Si open_infraction_pv=True → MediationDocument de type INFRACTION créé',                                  'Système'],
        ['Notification hiérarchie','Chef d\'Inspection et Directeur Régional notifiés par email et notification in-app',                    'Système'],
        ['Alerte tableau de bord', 'Compteur "Non-comparutions" incrémenté dans les KPIs de l\'interface admin',                              'Système'],
    ],
    header_bg='DC2626',
)

heading2('7.4 Escalade automatique (Celery)')
body(
    'La tâche Celery check_convocation_deadlines s\'exécute tous les jours à 07h00 et '
    'escalade automatiquement les séances dont l\'employeur n\'a pas accusé réception '
    'après 3 tentatives de relance sur une période de 96 heures (48h initiale + 3 × 24h).'
)

heading2('7.5 Tableau de bord des non-comparutions')
body('L\'interface d\'administration affiche :')
bullet('KPI "Non-comparutions" (rouge) — cliquable pour filtrer les séances concernées')
bullet('KPI "Sans accusé de réception" (orange) — séances dont l\'employeur n\'a pas répondu')
bullet('Fond rouge pâle sur les lignes de séance avec employer_no_show=True')
bullet('Bouton "Non-comparution" (rouge) sur chaque séance éligible')

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  8. WORKFLOW DES ACCORDS
# ════════════════════════════════════════════════════════════════════════════
heading1('8. Workflow des Accords')

heading2('8.1 Cycle de vie d\'un accord')
flow_table([
    ('DRAFT\n(Brouillon)',        'Accord rédigé\npar le médiateur'),
    ('PENDING_SIGNATURE\n(En attente)', 'Envoyé aux\nparties pour signature'),
    ('SIGNED\n(Signé)',           'Toutes signatures\nrecueillies'),
    ('EXECUTED\n(Exécuté)',       'Obligations\nrespectées'),
    ('BREACHED\n(Rompu)',         'Non-respect\nd\'une obligation'),
], color='166534')

heading2('8.2 Création et signature de l\'accord')
for step in [
    '1. L\'inspecteur rédige le texte de l\'accord (termes, obligations des deux parties, délai d\'exécution, montant indemnité si applicable).',
    '2. Via POST /mediations/agreements/, l\'accord est créé en statut DRAFT.',
    '3. Il est passé en PENDING_SIGNATURE via l\'action sign_agreement.',
    '4. Le travailleur signe via POST /mediations/agreements/{id}/sign/ (signer_role=employee + signature image).',
    '5. L\'employeur signe de la même manière (signer_role=employer).',
    '6. Le médiateur signe en dernier (signer_role=mediator).',
    '7. Dès que les 3 signatures sont collectées (is_fully_signed=True) → statut SIGNED.',
    '8. Un PDF de l\'accord signé est généré automatiquement et archivé.',
]:
    bullet(step)

heading2('8.3 Suivi de l\'exécution')
body(
    'La tâche Celery check_agreement_execution_deadlines s\'exécute chaque jour à 08h00 '
    'et envoie des rappels au médiateur et au plaignant si le délai d\'exécution approche '
    'ou est dépassé. En cas de non-respect constaté :'
)
for step in [
    'L\'inspecteur marque l\'accord comme rompu via POST /mediations/agreements/{id}/mark_breached/.',
    'Le statut de l\'accord passe à BREACHED.',
    'Le statut de la plainte passe automatiquement à JUDICIAL.',
    'Le médiateur et le Chef d\'Inspection sont notifiés.',
]:
    bullet(step)

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  9. PROCÉDURES JUDICIAIRES ET ESCALADE
# ════════════════════════════════════════════════════════════════════════════
heading1('9. Procédures Judiciaires et Escalade')

heading2('9.1 Cas de renvoi judiciaire')
status_table(
    ['Déclencheur', 'Statut plainte', 'Action requise'],
    [
        ['Médiation sans accord',                       'JUDICIAL',   'Dossier transmis au Tribunal du Travail d\'Abidjan ou tribunal régional compétent'],
        ['Accord rompu par l\'employeur',               'JUDICIAL',   'Engagement de poursuites judiciaires + transmission au parquet du travail'],
        ['Non-comparution × 3 après escalade',          'ESCALATED',  'Chef d\'Inspection peut décider du renvoi judiciaire'],
        ['Infraction grave constatée en médiation',     'JUDICIAL',   'Ouverture d\'un PV d\'infraction séparé'],
    ],
    header_bg='7C3AED',
)

heading2('9.2 Procédure d\'escalade hiérarchique')
for step in [
    '1. L\'inspecteur ou le système (Celery) déclenche l\'escalade.',
    '2. Une notification ComplaintNotification est créée pour le Chef d\'Inspection.',
    '3. Le Chef d\'Inspection reçoit un email et une notification in-app avec résumé du dossier.',
    '4. Si le Chef d\'Inspection ne traite pas sous 48h, l\'escalade monte au Directeur Régional.',
    '5. En cas d\'urgence, le Directeur Général est informé directement.',
]:
    bullet(step)

heading2('9.3 Score de conformité des entreprises')
body(
    'Le système maintient un score de conformité (compliance_score) pour chaque entreprise. '
    'Ce score est décrémenté automatiquement lors des infractions :'
)
status_table(
    ['Infraction', 'Impact score', 'Seuil d\'alerte'],
    [
        ['Non-comparution à une séance de médiation', '−15 points', 'Score < 50 → signalement automatique DGT'],
        ['Accord de médiation rompu',                 '−20 points', 'Score < 30 → mise sous surveillance renforcée'],
        ['Récidive sur même type d\'infraction',      '−10 points additionnels', ''],
    ],
    header_bg='DC2626',
)

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  10. TÂCHES CELERY AUTOMATIQUES
# ════════════════════════════════════════════════════════════════════════════
heading1('10. Tâches Celery automatiques')

heading2('10.1 Planification des tâches (CELERYBEAT_SCHEDULE)')
status_table(
    ['Tâche', 'Heure (UTC = Abidjan)', 'Fréquence', 'Description'],
    [
        ['check_convocation_deadlines',         '07h00',  'Quotidienne', 'Relance auto ou escalade des convocations sans réponse après délai'],
        ['send_session_reminders',              '06h30',  'Quotidienne', 'Rappel 24h avant la séance aux participants ayant accusé réception'],
        ['check_agreement_execution_deadlines', '08h00',  'Quotidienne', 'Alerte sur accords dont le délai d\'exécution approche ou est dépassé'],
        ['auto_escalate_long_pending_mediations','10h00', 'Quotidienne', 'Escalade des médiations bloquées depuis 30+ jours sans avancement'],
    ],
    header_bg='F47E1C',
)

heading2('10.2 Logique de check_convocation_deadlines')
body('Cette tâche traite les séances en statut SCHEDULED avec des participants dont acknowledged_at IS NULL :')
for step in [
    '1. Si la 1ère convocation date de + 48h et aucune relance → envoyer relance n°1 (EMAIL).',
    '2. Si dernière relance date de + 24h et relances < 3 → envoyer relance suivante (rotation canaux).',
    '3. Si 3 relances envoyées sans réponse → déclencher escalade hiérarchique.',
    '4. Escalade : ComplaintNotification au Chef d\'Inspection, statut plainte → ESCALATED.',
]:
    bullet(step)

heading2('10.3 Logique de send_session_reminders')
body(
    'Envoie un rappel EMAIL + SMS aux participants (acknowledged_at IS NOT NULL) '
    'dont la séance a lieu dans les prochaines 24 heures. '
    'Le rappel inclut : date, heure, lieu (ou lien visio), nom du médiateur, numéro de dossier.'
)

heading2('10.4 Logique de auto_escalate_long_pending_mediations')
body(
    'Identifie les séances en statut SCHEDULED dont la date de création dépasse 30 jours '
    'sans changement de statut et sans accusé de réception de l\'employeur. '
    'Déclenche automatiquement une escalade au Directeur Régional avec rapport de synthèse.'
)

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  11. RÉFÉRENTIEL DES ENDPOINTS API
# ════════════════════════════════════════════════════════════════════════════
heading1('11. Référentiel des endpoints API')

heading2('11.1 Médiations — Sessions')
status_table(
    ['Méthode', 'Endpoint', 'Description', 'Permission'],
    [
        ['GET',    '/mediations/sessions/',                          'Liste des séances',                          'INSPECTEUR+'],
        ['POST',   '/mediations/sessions/',                          'Créer une séance',                           'INSPECTEUR+'],
        ['GET',    '/mediations/sessions/{id}/',                     'Détail d\'une séance',                       'INSPECTEUR+'],
        ['PUT',    '/mediations/sessions/{id}/',                     'Modifier une séance',                        'INSPECTEUR+'],
        ['DELETE', '/mediations/sessions/{id}/',                     'Supprimer une séance',                       'ADMIN'],
        ['POST',   '/mediations/sessions/{id}/convoke/',             'Envoyer les convocations',                   'INSPECTEUR+'],
        ['GET',    '/mediations/sessions/acknowledge/{token}/',      'Accuser réception (lien email/SMS)',          'Public'],
        ['POST',   '/mediations/sessions/{id}/manual_acknowledge/',  'Confirmer réception manuellement',           'INSPECTEUR+'],
        ['POST',   '/mediations/sessions/{id}/relance/',             'Relancer les non-accusés',                   'INSPECTEUR+'],
        ['POST',   '/mediations/sessions/{id}/report_no_show/',      'Constater non-comparution employeur',        'INSPECTEUR+'],
        ['POST',   '/mediations/sessions/{id}/postpone/',            'Reporter la séance',                         'INSPECTEUR+'],
        ['POST',   '/mediations/sessions/{id}/start/',               'Démarrer la séance',                         'INSPECTEUR+'],
        ['POST',   '/mediations/sessions/{id}/complete/',            'Clôturer la séance',                         'INSPECTEUR+'],
        ['POST',   '/mediations/sessions/{id}/generate_minutes/',    'Générer le PV de séance',                    'INSPECTEUR+'],
        ['GET',    '/mediations/sessions/no_shows/',                 'Séances avec non-comparution',               'INSPECTEUR+'],
        ['GET',    '/mediations/sessions/pending_acknowledgment/',   'Séances sans accusé réception',              'INSPECTEUR+'],
    ],
    header_bg='1D4ED8',
)

heading2('11.2 Participants')
status_table(
    ['Méthode', 'Endpoint', 'Description', 'Permission'],
    [
        ['GET',  '/mediations/participants/',       'Liste des participants',         'INSPECTEUR+'],
        ['POST', '/mediations/participants/',       'Ajouter un participant',         'INSPECTEUR+'],
        ['GET',  '/mediations/participants/{id}/',  'Détail d\'un participant',       'INSPECTEUR+'],
        ['PUT',  '/mediations/participants/{id}/',  'Modifier un participant',        'INSPECTEUR+'],
        ['DELETE','/mediations/participants/{id}/', 'Supprimer un participant',       'INSPECTEUR+'],
    ],
    header_bg='0F766E',
)

heading2('11.3 Accords')
status_table(
    ['Méthode', 'Endpoint', 'Description', 'Permission'],
    [
        ['GET',  '/mediations/agreements/',                 'Liste des accords',            'INSPECTEUR+'],
        ['POST', '/mediations/agreements/',                 'Créer un accord',              'INSPECTEUR+'],
        ['GET',  '/mediations/agreements/{id}/',            'Détail d\'un accord',          'INSPECTEUR+'],
        ['PUT',  '/mediations/agreements/{id}/',            'Modifier un accord',           'INSPECTEUR+'],
        ['POST', '/mediations/agreements/{id}/sign/',       'Signer l\'accord',             'INSPECTEUR/EMPLOYE/EMPLOYEUR'],
        ['POST', '/mediations/agreements/{id}/mark_breached/','Marquer accord rompu',      'INSPECTEUR+'],
        ['GET',  '/mediations/agreements/{id}/generate_pdf/','Générer PDF accord',         'INSPECTEUR+'],
    ],
    header_bg='7C3AED',
)

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  12. NOTIFICATIONS MULTI-CANAL
# ════════════════════════════════════════════════════════════════════════════
heading1('12. Notifications multi-canal')

heading2('12.1 Architecture des notifications')
body(
    'Le module notifications.py (mediations/notifications.py) centralise tous les envois. '
    'Chaque tentative est journalisée dans le modèle ConvocationAttempt avec : '
    'canal, statut (SENT/DELIVERED/FAILED/BOUNCED), timestamp, ID de message fournisseur, détail erreur.'
)

heading2('12.2 Configuration des fournisseurs SMS')
body('Les fournisseurs SMS sont configurables dans settings.py :')
status_table(
    ['Paramètre', 'Valeur par défaut', 'Description'],
    [
        ['SMS_GATEWAY_URL',       'Simulation (log)',          'URL de l\'API du fournisseur SMS'],
        ['SMS_GATEWAY_KEY',       'Non configuré',             'Clé API du fournisseur'],
        ['SMS_SENDER_ID',         'EINSPECTION',               'Identifiant affiché sur le téléphone du destinataire'],
        ['FRONTEND_URL',          'https://e-inspection.ci',   'URL de base pour les liens dans les SMS et emails'],
    ],
    header_bg='F47E1C',
)

heading2('12.3 Contenu des convocations')
body('Email de convocation — Informations incluses :')
for item in [
    'Numéro de plainte',
    'Date et heure de la séance',
    'Lieu (adresse complète ou lien visio)',
    'Nom et coordonnées du médiateur',
    'Lien d\'accusé de réception (UUID unique)',
    'Avertissement légal (Code du Travail art. 81)',
    'Coordonnées de l\'Inspection du Travail',
]:
    bullet(item)

heading2('12.4 Hiérarchie des notifications in-app')
status_table(
    ['Événement', 'Destinataire(s)', 'Type'],
    [
        ['Plainte déposée',              'Inspecteur du district',       'INFO'],
        ['Plainte assignée',             'Inspecteur + Plaignant',        'INFO'],
        ['Convocation envoyée',          'Toutes les parties',            'INFO'],
        ['Accusé de réception reçu',     'Médiateur',                     'SUCCESS'],
        ['3 relances sans réponse',      'Chef d\'Inspection + Médiateur', 'WARNING'],
        ['Non-comparution constatée',    'Chef d\'Inspection + Dir. Rég.', 'CRITICAL'],
        ['Accord signé',                 'Toutes les parties + DGT',      'SUCCESS'],
        ['Accord rompu',                 'Médiateur + Chef d\'Inspection', 'CRITICAL'],
        ['Délai accord dépassé',         'Médiateur + Plaignant',         'WARNING'],
        ['Séance dans 24h',              'Parties ayant accusé réception', 'REMINDER'],
    ],
    header_bg='1D4ED8',
)

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
#  13. SÉCURITÉ ET CONFORMITÉ
# ════════════════════════════════════════════════════════════════════════════
heading1('13. Sécurité et conformité')

heading2('13.1 Authentification et autorisation')
status_table(
    ['Mécanisme', 'Détail'],
    [
        ['JWT Access Token',    'Durée : 60 minutes — inclus dans l\'en-tête Authorization: Bearer'],
        ['JWT Refresh Token',   'Durée : 7 jours — rotation automatique à chaque rafraîchissement'],
        ['OTP 2FA',             'Code à 6 chiffres (TOTP) requis pour les rôles INSPECTEUR et supérieurs'],
        ['Tokens publics UUID', 'Jetons d\'accusé de réception sans auth, valables 30 jours, usage unique'],
        ['RBAC',                '8 rôles, contrôle au niveau de chaque action DRF via IsAuthenticated + permission custom'],
    ],
    header_bg='DC2626',
)

heading2('13.2 Protection des données (RGPD / Loi ivoirienne n° 2013-450)')
for item in [
    'Données des plaintes et des parties : accès restreint aux agents habilités',
    'Numéros de téléphone et emails chiffrés at-rest (AES-256)',
    'Logs d\'accès conservés 5 ans',
    'Droit à l\'oubli : procédure d\'anonymisation disponible pour le DGT',
    'Transferts de données : chiffrement TLS 1.3 obligatoire (HTTPS)',
]:
    bullet(item)

heading2('13.3 Traçabilité et audit')
for item in [
    'Chaque action de l\'API est journalisée (who, what, when, IP)',
    'Chaque envoi de convocation est enregistré dans ConvocationAttempt',
    'Chaque changement de statut de plainte est horodaté',
    'Les signatures électroniques d\'accords incluent le timestamp et l\'identité du signataire',
    'Les PV de carence générés sont archivés et non modifiables',
]:
    bullet(item)

heading2('13.4 Disponibilité et continuité de service')
status_table(
    ['Composant', 'SLA cible', 'Fallback'],
    [
        ['API backend',         '99.5% disponibilité',  'Load balancer + 2 instances'],
        ['Base de données',     '99.9%',                 'Réplication MySQL + sauvegarde quotidienne'],
        ['File Celery (Redis)', '99%',                   'Persistance Redis AOF'],
        ['Gateway SMS',         'Best-effort',           'Rotation fournisseurs (Orange CI → MTN CI → Moov)'],
    ],
    header_bg='009A44',
)

# ── Pied de document ─────────────────────────────────────────────────────────
doc.add_page_break()
p = doc.add_paragraph()
p.clear()
run = p.add_run(f'Document généré le {date.today().strftime("%d/%m/%Y")} — Plateforme e-Inspection du Travail CI — Confidentiel')
run.font.size   = Pt(8)
run.font.color.rgb = GRIS
run.italic = True
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

out = r'c:\Users\HP\Desktop\projets\plateforme-travail\backend\Workflows_Mediations_Conciliations.docx'
doc.save(out)
print(f'OK  Document genere : {out}')

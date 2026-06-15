"""
Génération de l'offre commerciale Word – Plateforme Nationale e-Inspection du Travail
Destinataire : Direction Générale du Travail – Côte d'Ivoire
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime


# ── Palette ─────────────────────────────────────────────────────────────────
BLEU_FONCE  = RGBColor(0x00, 0x34, 0x7C)
BLEU_MOYEN  = RGBColor(0x00, 0x72, 0xC6)
BLEU_CLAIR  = RGBColor(0xDC, 0xEA, 0xF8)
ORANGE_CI   = RGBColor(0xF4, 0x7E, 0x1C)   # orange Côte d'Ivoire
VERT_CI     = RGBColor(0x00, 0x9A, 0x44)   # vert Côte d'Ivoire
BLANC       = RGBColor(0xFF, 0xFF, 0xFF)
GRIS_CLAIR  = RGBColor(0xF5, 0xF7, 0xFA)
GRIS_TEXTE  = RGBColor(0x2D, 0x2D, 0x2D)
GRIS_MOYEN  = RGBColor(0x66, 0x66, 0x66)

TODAY       = datetime.date.today()
REF         = 'OC-DGT-CI-2026-001'
VALID_DATE  = (TODAY + datetime.timedelta(days=90)).strftime('%d %B %Y')


# ── Helpers ──────────────────────────────────────────────────────────────────
def cell_bg(cell, hex6: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex6)
    tcPr.append(shd)


def add_hr(doc, color='00347C', thick=6):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pb = OxmlElement('w:pBdr')
    b  = OxmlElement('w:bottom')
    b.set(qn('w:val'),   'single')
    b.set(qn('w:sz'),    str(thick))
    b.set(qn('w:space'), '1')
    b.set(qn('w:color'), color)
    pb.append(b)
    pPr.append(pb)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(2)


def h1(doc, text, color=BLEU_FONCE, size=15, sb=20, sa=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after  = Pt(sa)
    r = p.add_run(text)
    r.bold = True; r.font.size = Pt(size)
    r.font.color.rgb = color; r.font.name = 'Calibri'
    return p


def h2(doc, text, color=BLEU_MOYEN, size=12, sb=10, sa=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after  = Pt(sa)
    r = p.add_run(text)
    r.bold = True; r.font.size = Pt(size)
    r.font.color.rgb = color; r.font.name = 'Calibri'
    return p


def h3(doc, text, color=GRIS_TEXTE, size=11, sb=6, sa=3):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after  = Pt(sa)
    r = p.add_run(text)
    r.bold = True; r.font.size = Pt(size)
    r.font.color.rgb = color; r.font.name = 'Calibri'
    return p


def body(doc, text, size=10.5, italic=False, color=GRIS_TEXTE, sb=3, sa=3,
         align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after  = Pt(sa)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    r = p.add_run(text)
    r.font.size = Pt(size); r.font.color.rgb = color
    r.font.name = 'Calibri'; r.italic = italic
    return p


def bul(doc, text, size=10.5, color=GRIS_TEXTE, bold=False):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)
    r = p.add_run(text)
    r.font.size = Pt(size); r.font.color.rgb = color
    r.font.name = 'Calibri'; r.bold = bold
    return p


def num_list(doc, text, size=10.5, color=GRIS_TEXTE):
    p = doc.add_paragraph(style='List Number')
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)
    r = p.add_run(text)
    r.font.size = Pt(size); r.font.color.rgb = color; r.font.name = 'Calibri'
    return p


def tbl_header_row(row, headers, bg='00347C', txt_color=BLANC, size=10, bold=True):
    for i, h in enumerate(headers):
        c = row.cells[i]
        cell_bg(c, bg)
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after  = Pt(6)
        r = p.add_run(h)
        r.bold = bold; r.font.size = Pt(size)
        r.font.color.rgb = txt_color; r.font.name = 'Calibri'


def tbl_data_cell(cell, text, bg='FFFFFF', txt_color=GRIS_TEXTE, size=9.5,
                  bold=False, align=WD_ALIGN_PARAGRAPH.LEFT, sb=4, sa=4):
    cell_bg(cell, bg)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after  = Pt(sa)
    r = p.add_run(text)
    r.bold = bold; r.font.size = Pt(size)
    r.font.color.rgb = txt_color; r.font.name = 'Calibri'


def banner(doc, text, bg='00347C', txt_color=BLANC, size=11, sb=8, sa=8):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    cell_bg(c, bg)
    c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after  = Pt(sa)
    r = p.add_run('  ' + text)
    r.bold = True; r.font.size = Pt(size)
    r.font.color.rgb = txt_color; r.font.name = 'Calibri'
    return t


def pb(doc):
    doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
doc = Document()

for section in doc.sections:
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.0)

# ════════════════════════════════════════════════════════════════════════════
# PAGE DE GARDE
# ════════════════════════════════════════════════════════════════════════════

# Bandeau tricolore CI (orange – blanc – vert)
t_tri = doc.add_table(rows=1, cols=3)
t_tri.alignment = WD_TABLE_ALIGNMENT.CENTER
colors_ci = ['F47E1C', 'FFFFFF', '009A44']
for i, col in enumerate(colors_ci):
    c = t_tri.rows[0].cells[i]
    cell_bg(c, col)
    c.paragraphs[0].paragraph_format.space_before = Pt(4)
    c.paragraphs[0].paragraph_format.space_after  = Pt(4)
    c.width = Cm(5.5)

doc.add_paragraph()

# Bandeau institutionnel
t_inst = doc.add_table(rows=1, cols=1)
t_inst.alignment = WD_TABLE_ALIGNMENT.CENTER
ci = t_inst.rows[0].cells[0]
cell_bg(ci, '00347C')
ci.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
p = ci.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(14)
p.paragraph_format.space_after  = Pt(4)
r = p.add_run('RÉPUBLIQUE DE CÔTE D\'IVOIRE')
r.bold = True; r.font.size = Pt(14)
r.font.color.rgb = BLANC; r.font.name = 'Calibri'

p2 = ci.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
p2.paragraph_format.space_before = Pt(0)
p2.paragraph_format.space_after  = Pt(4)
r2 = p2.add_run('Union – Discipline – Travail')
r2.font.size = Pt(10); r2.italic = True
r2.font.color.rgb = RGBColor(0xCC, 0xDD, 0xFF); r2.font.name = 'Calibri'

p3 = ci.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
p3.paragraph_format.space_before = Pt(0)
p3.paragraph_format.space_after  = Pt(14)
r3 = p3.add_run('Ministère de l\'Emploi et de la Protection Sociale')
r3.font.size = Pt(12)
r3.font.color.rgb = RGBColor(0xE0, 0xEC, 0xFF); r3.font.name = 'Calibri'

doc.add_paragraph()

# Grand titre
for line, size, color in [
    ('OFFRE COMMERCIALE',             32, BLEU_FONCE),
    ('Plateforme Nationale',          24, ORANGE_CI),
    ('e-Inspection du Travail',       24, VERT_CI),
    ('— Côte d\'Ivoire —',           14, GRIS_MOYEN),
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    r = p.add_run(line)
    r.bold = True; r.font.size = Pt(size)
    r.font.color.rgb = color; r.font.name = 'Calibri'

add_hr(doc, 'F47E1C', thick=8)
doc.add_paragraph()

# Encadré sous-titre
t_st = doc.add_table(rows=1, cols=1)
t_st.alignment = WD_TABLE_ALIGNMENT.CENTER
cst = t_st.rows[0].cells[0]
cell_bg(cst, 'DCF0FF')
cst.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
cst.paragraphs[0].paragraph_format.space_before = Pt(12)
cst.paragraphs[0].paragraph_format.space_after  = Pt(12)
rst = cst.paragraphs[0].add_run(
    'Solution intégrée de digitalisation de l\'inspection du travail,\n'
    'de gestion des plaintes sociales, de médiation et de conciliation\n'
    'pour la Direction Générale du Travail de Côte d\'Ivoire'
)
rst.font.size = Pt(12); rst.italic = True
rst.font.color.rgb = BLEU_FONCE; rst.font.name = 'Calibri'

doc.add_paragraph()

# Fiche de couverture
t_fiche = doc.add_table(rows=7, cols=2)
t_fiche.alignment = WD_TABLE_ALIGNMENT.CENTER
t_fiche.style = 'Table Grid'
fiche_data = [
    ('Destinataire',    'Direction Générale du Travail (DGT) – Ministère de l\'Emploi et de la Protection Sociale'),
    ('Adresse',         'Plateau, Avenue Terrasson de Fougères, Abidjan – Côte d\'Ivoire'),
    ('Préparé par',     'Numerix Digital  |  franckalain.ai@gmail.com'),
    ('Référence',       REF),
    ('Date d\'émission', TODAY.strftime('%d %B %Y')),
    ('Validité',        f'90 jours – jusqu\'au {VALID_DATE}'),
    ('Classification',  'CONFIDENTIEL – Usage exclusif de la Direction Générale du Travail'),
]
for i, (lbl, val) in enumerate(fiche_data):
    row = t_fiche.rows[i]
    cell_bg(row.cells[0], '00347C')
    cell_bg(row.cells[1], 'F5F7FA' if i % 2 == 0 else 'FFFFFF')
    for col, txt in [(0, lbl), (1, val)]:
        c = row.cells[col]
        c.paragraphs[0].paragraph_format.space_before = Pt(6)
        c.paragraphs[0].paragraph_format.space_after  = Pt(6)
        r = c.paragraphs[0].add_run(txt)
        r.bold = (col == 0); r.font.size = Pt(10)
        r.font.color.rgb = BLANC if col == 0 else (ORANGE_CI if i == 6 else GRIS_TEXTE)
        r.font.name = 'Calibri'

doc.add_paragraph()
add_hr(doc, 'F47E1C', thick=6)

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# SOMMAIRE
# ════════════════════════════════════════════════════════════════════════════
h1(doc, 'TABLE DES MATIÈRES', size=16, sb=0)
add_hr(doc)
doc.add_paragraph()

sommaire = [
    ('1', 'Résumé Exécutif',                              '4'),
    ('2', 'Contexte et Enjeux',                           '5'),
    ('3', 'Vision et Objectifs Stratégiques',             '7'),
    ('4', 'Présentation de la Solution',                  '8'),
    ('5', 'Fonctionnalités Détaillées (16 modules)',      '10'),
    ('6', 'Architecture Technique et Sécurité',           '18'),
    ('7', 'Plan de Déploiement (4 phases – 18 mois)',     '20'),
    ('8', 'Formation et Accompagnement au Changement',    '22'),
    ('9', 'Offre Financière Détaillée',                   '23'),
    ('10', 'Niveaux de Service (SLA)',                    '26'),
    ('11', 'Notre Entreprise et Équipe Projet',           '27'),
    ('12', 'Proposition de Valeur Différenciante',        '29'),
    ('13', 'Conditions Générales et Juridiques',          '30'),
    ('14', 'Annexes Techniques',                          '32'),
]

for num, titre, page in sommaire:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(14.5), WD_ALIGN_PARAGRAPH.RIGHT)
    r1 = p.add_run(f'{num}.   {titre}')
    r1.font.size = Pt(11); r1.font.color.rgb = BLEU_FONCE; r1.font.name = 'Calibri'
    r2 = p.add_run(f'\t{page}')
    r2.bold = True; r2.font.size = Pt(11)
    r2.font.color.rgb = ORANGE_CI; r2.font.name = 'Calibri'

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 1. RÉSUMÉ EXÉCUTIF
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '1.  RÉSUMÉ EXÉCUTIF', sb=0)
add_hr(doc)

body(doc,
    'Numerix Digital présente à la Direction Générale du Travail (DGT) de Côte d\'Ivoire la présente '
    'offre commerciale pour la conception, le déploiement et la maintenance de la Plateforme Nationale '
    'e-Inspection du Travail. Cette solution digitale de bout en bout vise à transformer en profondeur '
    'les processus de l\'inspection du travail, à renforcer la protection des travailleurs ivoiriens '
    'et à moderniser la relation entre l\'administration du travail, les employeurs et les salariés.')

body(doc,
    'La Côte d\'Ivoire, premier acteur économique de l\'UEMOA avec un PIB en progression constante, '
    'connaît une croissance soutenue de son marché de l\'emploi formel et informel. Cette dynamique '
    's\'accompagne d\'une augmentation des besoins de régulation et de protection sociale, appelant '
    'une modernisation urgente des outils à disposition de la Direction Générale du Travail.')

doc.add_paragraph()

# KPIs clés attendus
t_kpi = doc.add_table(rows=2, cols=4)
t_kpi.alignment = WD_TABLE_ALIGNMENT.CENTER
kpi_data = [
    ('60 %', 'Réduction du délai moyen\nde traitement des plaintes'),
    ('100 %', 'Traçabilité numérique\nde toutes les procédures'),
    ('24/7', 'Accessibilité du portail\ncitoyen en ligne'),
    ('400+', 'Agents formés à\nla plateforme sur 18 mois'),
]
for j, (val, lbl) in enumerate(kpi_data):
    cv = t_kpi.rows[0].cells[j]
    cl = t_kpi.rows[1].cells[j]
    cell_bg(cv, '00347C')
    cell_bg(cl, 'DCF0FF')
    pv = cv.paragraphs[0]
    pv.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pv.paragraph_format.space_before = Pt(10)
    pv.paragraph_format.space_after  = Pt(10)
    rv = pv.add_run(val)
    rv.bold = True; rv.font.size = Pt(20)
    rv.font.color.rgb = ORANGE_CI; rv.font.name = 'Calibri'
    pl = cl.paragraphs[0]
    pl.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pl.paragraph_format.space_before = Pt(6)
    pl.paragraph_format.space_after  = Pt(6)
    rl = pl.add_run(lbl)
    rl.font.size = Pt(9); rl.font.color.rgb = BLEU_FONCE; rl.font.name = 'Calibri'

doc.add_paragraph()

body(doc,
    'La solution proposée couvre l\'intégralité du cycle de vie d\'une plainte de travail — de sa '
    'saisie numérique par le travailleur jusqu\'à la décision judiciaire — en passant par '
    'l\'enquête de l\'inspecteur, la médiation, la conciliation et le recours hiérarchique. '
    'Elle intègre également des outils d\'intelligence artificielle, un observatoire statistique '
    'et un système de gestion électronique des documents (GED) conforme aux standards internationaux.')

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 2. CONTEXTE ET ENJEUX
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '2.  CONTEXTE ET ENJEUX', sb=0)
add_hr(doc)

h2(doc, '2.1  Le marché du travail en Côte d\'Ivoire')
body(doc,
    'La Côte d\'Ivoire compte plus de 8 millions d\'actifs dans le secteur structuré (formel et '
    'informel encadré), avec une progression annuelle de l\'emploi salarié de l\'ordre de 5 à 7 %. '
    'Les secteurs clés — agro-industrie, BTP, services financiers, télécommunications, commerce — '
    'génèrent un volume croissant de relations contractuelles de travail et, corrélativement, '
    'une augmentation des litiges sociaux.')

body(doc,
    'Le Code du Travail ivoirien (Loi n° 2015-532 du 20 juillet 2015) et ses textes d\'application '
    'confèrent à l\'inspection du travail un rôle central dans la régulation des relations '
    'professionnelles. Or, la DGT et ses directions régionales disposent encore de moyens de '
    'traitement principalement manuels et papier, inadaptés au volume et à la complexité croissants '
    'des situations à traiter.')

h2(doc, '2.2  Diagnostic de la situation actuelle')
defis_detail = [
    ('Gestion fragmentée des plaintes',
     'Les plaintes sont reçues par courrier, par téléphone ou en personne sans système centralisé, '
     'ce qui génère des pertes d\'information, des doublons et une incapacité à garantir la '
     'traçabilité du traitement au plaignant.'),
    ('Absence de registre numérique des entreprises',
     'L\'identification des entreprises, leur secteur, leur taille, leur historique de contrôle '
     'et leur niveau de conformité ne font l\'objet d\'aucune base de données consolidée. '
     'Chaque direction régionale travaille en silo.'),
    ('Communication inter-institutionnelle défaillante',
     'Les échanges entre inspecteurs de terrain, chefs d\'inspection, directeurs régionaux et '
     'direction centrale s\'effectuent par notes de service papier ou e-mails non sécurisés, '
     'générant des délais et des risques de perte d\'information.'),
    ('Statistiques sociales peu fiables',
     'L\'absence d\'outil de collecte standardisée rend difficile la production de statistiques '
     'fiables sur les accidents du travail, les infractions relevées, les taux de résolution '
     'des conflits, nécessaires aux rapports de l\'OIT et à la politique sociale du gouvernement.'),
    ('Médiation et conciliation non dématérialisées',
     'Les procédures de médiation et de conciliation exigent de nombreuses convocations '
     'physiques et produisent des procès-verbaux papier difficiles à archiver et à exploiter.'),
    ('Travailleurs domestiques non couverts',
     'Le secteur du travail domestique — estimé à plus de 400 000 personnes en Côte d\'Ivoire — '
     'reste largement en dehors des dispositifs de protection et de contrôle de l\'inspection '
     'du travail, faute d\'outils adaptés.'),
]
for titre, desc in defis_detail:
    h3(doc, f'• {titre}')
    body(doc, desc)

h2(doc, '2.3  Cadre réglementaire et opportunité')
body(doc,
    'La Stratégie Nationale de Développement Numérique de la Côte d\'Ivoire (SND-CI 2021-2025) '
    'et le Plan National de Développement (PND 2021-2025) placent la dématérialisation des services '
    'publics au cœur des priorités gouvernementales. La digitalisation de l\'inspection du travail '
    's\'inscrit dans cette dynamique et répond aux recommandations du Bureau International du '
    'Travail (BIT/OIT) visant à renforcer les systèmes d\'inspection nationaux.')

body(doc,
    'Par ailleurs, les engagements de la Côte d\'Ivoire dans le cadre du Compact avec l\'Afrique '
    '(CWA) et des accords de partenariat économique (APE) avec l\'Union Européenne imposent des '
    'standards de gouvernance sociale et de transparence que seule une plateforme numérique '
    'dédiée peut permettre d\'atteindre et de démontrer.')

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 3. VISION ET OBJECTIFS STRATÉGIQUES
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '3.  VISION ET OBJECTIFS STRATÉGIQUES', sb=0)
add_hr(doc)

body(doc,
    'Notre vision : faire de la Direction Générale du Travail de Côte d\'Ivoire un modèle '
    'africain d\'administration du travail numérique, accessible, transparente et efficace '
    'au service des travailleurs et des employeurs.',
    italic=True, color=BLEU_MOYEN, size=12)

doc.add_paragraph()

objectifs = [
    ('OBJ-01', 'Accessibilité citoyenne',
     'Permettre à tout travailleur ivoirien — y compris dans les zones rurales — de déposer '
     'une plainte, suivre son dossier et être informé des décisions, depuis un téléphone '
     'mobile, sans se déplacer.'),
    ('OBJ-02', 'Efficacité administrative',
     'Réduire le délai moyen de traitement d\'une plainte de 6 mois à moins de 45 jours '
     'grâce à l\'automatisation des workflow, aux alertes et aux tableaux de bord de pilotage.'),
    ('OBJ-03', 'Renforcement du droit du travail',
     'Outiller les inspecteurs du travail pour qu\'ils puissent exercer leur mission de '
     'contrôle plus efficacement, en ciblant les entreprises à risque et en documentant '
     'numériquement leurs constats.'),
    ('OBJ-04', 'Pilotage basé sur les données',
     'Fournir à la Direction Générale un observatoire des statistiques sociales en temps '
     'réel, permettant d\'orienter la politique du travail sur des données fiables et de '
     'produire les rapports requis par l\'OIT et les partenaires internationaux.'),
    ('OBJ-05', 'Interopérabilité',
     'Connecter la plateforme aux systèmes existants : CNPS (Caisse Nationale de Prévoyance '
     'Sociale), DGI, RCCM (greffe des tribunaux de commerce), et à terme au portail '
     'unique des services publics e-services.ci.'),
    ('OBJ-06', 'Protection des catégories vulnérables',
     'Couvrir spécifiquement les travailleurs domestiques, les travailleurs migrants et '
     'les travailleurs de l\'économie informelle encadrée par des modules dédiés.'),
]

t_obj = doc.add_table(rows=len(objectifs), cols=3)
t_obj.style = 'Table Grid'
t_obj.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, (ref, titre, desc) in enumerate(objectifs):
    row = t_obj.rows[i]
    bg = 'F5F7FA' if i % 2 == 0 else 'FFFFFF'
    tbl_data_cell(row.cells[0], ref,   bg='00347C', txt_color=BLANC, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    tbl_data_cell(row.cells[1], titre, bg=bg,       txt_color=BLEU_FONCE, bold=True)
    tbl_data_cell(row.cells[2], desc,  bg=bg,       txt_color=GRIS_TEXTE)

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 4. PRÉSENTATION DE LA SOLUTION
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '4.  PRÉSENTATION DE LA SOLUTION', sb=0)
add_hr(doc)

body(doc,
    'La Plateforme Nationale e-Inspection du Travail est une solution web full-stack et mobile '
    'multi-acteurs, accessible en Français et pensée pour les contextes d\'usage ivoiriens '
    '(connexion mobile 3G/4G, usages sur smartphone, diversité des profils d\'utilisateurs). '
    'Elle centralise l\'ensemble des processus de l\'inspection du travail en un écosystème '
    'numérique cohérent, de la réception d\'une plainte à sa résolution définitive.')

h2(doc, '4.1  Architecture fonctionnelle globale')
body(doc,
    'La plateforme s\'articule autour de trois espaces distincts accessibles via un portail web '
    'responsive et une application mobile iOS/Android :')

espaces = [
    ('Portail Citoyen (public)',
     'Espace accessible sans authentification forte pour les travailleurs et employeurs. '
     'Permet le dépôt de plaintes en ligne, le suivi de dossier par numéro de référence, '
     'la consultation des textes réglementaires et la prise de contact avec les services.'),
    ('Espace Métier (agents DGT)',
     'Espace sécurisé réservé aux agents de la DGT : inspecteurs, chefs d\'inspection, '
     'directeurs régionaux, médiateurs, agents judiciaires. Accès par authentification '
     'JWT renforcée avec OTP à deux facteurs.'),
    ('Console d\'Administration',
     'Espace de paramétrage, de supervision technique et d\'audit réservé aux '
     'administrateurs système. Gestion des utilisateurs, des droits, des configurations '
     'et des journaux d\'activité.'),
]
for titre, desc in espaces:
    h3(doc, f'▶  {titre}')
    body(doc, desc)

h2(doc, '4.2  Les acteurs de la plateforme')
acteurs_data = [
    ('Acteur', 'Profil', 'Rôle principal', 'Canal d\'accès'),
    ('Travailleur / Salarié',    '8M+ actifs',       'Dépôt plainte, suivi dossier',          'Web + App mobile'),
    ('Employé domestique',       '400K+',             'Inscription, contrat, certification',   'App mobile'),
    ('Employeur / Entreprise',   '150K entreprises',  'Réponse plainte, conformité',           'Web'),
    ('Inspecteur du Travail',    '~600 agents',       'Enquête, contrôle, PV numérique',       'Web + App mobile'),
    ('Chef d\'Inspection',       '~80 chefs',         'Validation, supervision, affectation',  'Web'),
    ('Directeur Régional',       '19 directions',     'Pilotage régional, escalades',          'Web'),
    ('Directeur Général',        '1',                 'Pilotage national, reporting',          'Web'),
    ('Médiateur/Conciliateur',   '~50',               'Conduite séances médiation',            'Web + Visio'),
    ('Agent judiciaire',         '~30',               'Suivi procédures judiciaires',          'Web'),
    ('Administrateur système',   '5–10',              'Config, audit, sécurité',               'Console admin'),
]
t_act = doc.add_table(rows=len(acteurs_data), cols=4)
t_act.style = 'Table Grid'
t_act.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(acteurs_data):
    row = t_act.rows[i]
    bg = '00347C' if i == 0 else ('F5F7FA' if i % 2 == 0 else 'FFFFFF')
    tc = BLANC if i == 0 else GRIS_TEXTE
    for j, txt in enumerate(row_data):
        c = row.cells[j]
        cell_bg(c, bg)
        c.paragraphs[0].paragraph_format.space_before = Pt(5)
        c.paragraphs[0].paragraph_format.space_after  = Pt(5)
        r = c.paragraphs[0].add_run(txt)
        r.bold = (i == 0 or j == 0); r.font.size = Pt(9.5 if i > 0 else 9)
        r.font.color.rgb = tc; r.font.name = 'Calibri'

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 5. FONCTIONNALITÉS DÉTAILLÉES
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '5.  FONCTIONNALITÉS DÉTAILLÉES (16 MODULES)', sb=0)
add_hr(doc)

body(doc,
    'La plateforme est organisée en 16 modules fonctionnels couvrant l\'intégralité des '
    'besoins opérationnels et stratégiques de la Direction Générale du Travail.')

# ── Module 1 ─────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 1  –  Gestion des Utilisateurs et des Accès', bg='00347C')
h2(doc, 'Objectif : Sécuriser et fluidifier l\'accès à la plateforme pour tous les profils')
bul(doc, 'Système multi-rôles avec 8 types d\'utilisateurs (travailleur, employeur, inspecteur, chef, directeur régional, DG, médiateur, admin)')
bul(doc, 'Authentification par JWT (JSON Web Token) avec durée de session configurable')
bul(doc, 'Authentification à deux facteurs (OTP via SMS/Google Authenticator) obligatoire pour les agents DGT')
bul(doc, 'Vérification d\'identité par e-mail lors de l\'inscription (lien d\'activation à durée limitée)')
bul(doc, 'Réinitialisation sécurisée du mot de passe avec token à usage unique')
bul(doc, 'Gestion des profils complets : informations personnelles, photo, documents d\'identité, spécialisation')
bul(doc, 'Numéros de téléphone ivoiriens validés (indicatif +225) et opérateurs reconnus (Orange CI, MTN CI, Moov Africa)')
bul(doc, 'Annuaire interne des agents DGT avec filtre par zone géographique et spécialité')
bul(doc, 'Délégation temporaire de rôle (ex : suppléance lors d\'un congé)')
bul(doc, 'Journal de connexion et de déconnexion de chaque utilisateur avec IP et horodatage')

# ── Module 2 ─────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 2  –  Registre National des Entreprises', bg='006BAF')
h2(doc, 'Objectif : Centraliser le référentiel de toutes les entreprises assujetties au Code du Travail')
bul(doc, 'Fiche d\'identité complète : raison sociale, RCCM, NIF, numéro CNPS, secteur d\'activité (code NACE/CITI)')
bul(doc, 'Formes juridiques : SARL, SA, SAS, EI, SASU, SNC, GIE, coopérative et autres')
bul(doc, 'Gestion multi-établissements : siège social + succursales avec liens hiérarchiques')
bul(doc, 'Géolocalisation précise (latitude/longitude) et affectation automatique à la zone d\'inspection')
bul(doc, 'Score de conformité dynamique (0–100) calculé à partir de l\'historique des contrôles et infractions')
bul(doc, 'Niveau de risque : Faible / Moyen / Élevé / Critique, avec plan de contrôle priorisé')
bul(doc, 'Stockage sécurisé des documents légaux : statuts, RCCM, procès-verbaux des AG, bilans sociaux')
bul(doc, 'Historique complet des inspections et des plaintes par entreprise')
bul(doc, 'Indicateurs RH : nombre de salariés (CDI, CDD, intérim, apprentis), masse salariale déclarée')
bul(doc, 'Import en masse depuis Excel/CSV pour migration de l\'existant')
bul(doc, 'Interface de recherche avancée : par secteur, taille, zone, niveau de risque, date de dernier contrôle')

# ── Module 3 ─────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 3  –  Gestion des Plaintes Sociales', bg='00347C')
h2(doc, 'Objectif : Numériser et accélérer le traitement de l\'ensemble des plaintes de travail')
bul(doc, '11 types de plaintes : salaires impayés, licenciement abusif, harcèlement moral, harcèlement sexuel, accident du travail, heures supplémentaires non rémunérées, violation du droit aux congés, non-respect du contrat, discrimination, conditions de travail dangereuses, autres')
bul(doc, 'Numérotation automatique et unique : PLT-CI-AAAA-XXXXXX (traçabilité nationale)')
bul(doc, 'Workflow configurable en 9 statuts : Reçue → Assignée → En cours → En investigation → En médiation → Résolue / Clôturée / Escaladée / Judiciaire')
bul(doc, '4 niveaux de priorité : Normal, Moyen, Élevé, Urgent — avec escalade automatique si délai dépassé')
bul(doc, 'Pièces jointes multi-formats : PDF, images (JPG/PNG), vidéos (MP4), enregistrements audio (MP3/WAV), taille max configurable')
bul(doc, 'Suivi en temps réel pour le plaignant : notifications SMS et e-mail à chaque changement de statut')
bul(doc, 'Fil de commentaires interne entre les agents DGT traitant le dossier')
bul(doc, 'Journal d\'audit immuable : tous les changements d\'état sont horodatés et associés à un agent nommément identifié')
bul(doc, 'Délais réglementaires configurables avec alertes automatiques pour les responsables')
bul(doc, 'Tableau de bord des plaintes en attente, classées par ancienneté et priorité')
bul(doc, 'Statistiques de performance par inspecteur, par zone et par type de plainte')

# ── Module 4 ─────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 4  –  Zones et Planification des Inspections', bg='006BAF')
h2(doc, 'Objectif : Organiser géographiquement les missions de contrôle sur l\'ensemble du territoire')
bul(doc, 'Découpage national en zones d\'inspection : 19 directions régionales, communes, sous-préfectures')
bul(doc, 'Affectation des inspecteurs à leurs zones de compétence avec possibilité de zones partagées')
bul(doc, 'Planification des missions d\'inspection : programmées, inopinées, de contrôle-suite')
bul(doc, 'Agenda de l\'inspecteur avec synchronisation calendrier (iCal/Google Calendar)')
bul(doc, 'Feuille de route numérique pour les tournées (liste d\'entreprises à visiter, adresse GPS)')
bul(doc, 'Rapport de visite numérique avec saisie sur tablette/smartphone (hors connexion possible)')
bul(doc, 'Procès-verbal d\'infraction numérique avec signature électronique de l\'inspecteur')
bul(doc, 'Mise en demeure et suivi des délais de mise en conformité')
bul(doc, 'Cartographie des zones d\'inspection avec densité des entreprises et des plaintes')

# ── Module 5 ─────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 5  –  Workflow Hiérarchique et Approbations', bg='00347C')
h2(doc, 'Objectif : Digitaliser les circuits de validation et d\'approbation à tous les niveaux')
bul(doc, 'Chaîne d\'approbation configurable : Inspecteur → Chef d\'Inspection → Directeur Régional → Direction Nationale')
bul(doc, 'Délégation de signature : un responsable peut déléguer ses pouvoirs d\'approbation pendant une période définie')
bul(doc, 'Escalade automatique : si le valideur ne répond pas dans le délai imparti, le dossier remonte au niveau supérieur avec alerte')
bul(doc, 'Notification en temps réel de chaque demande d\'approbation (e-mail + notification in-app)')
bul(doc, 'Annotations et commentaires à chaque étape de validation')
bul(doc, 'Tableau de bord des approbations en attente avec ancienneté et priorité')
bul(doc, 'Historique complet de toutes les décisions hiérarchiques avec justificatifs')

# ── Module 6 ─────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 6  –  Médiation et Conciliation', bg='006BAF')
h2(doc, 'Objectif : Gérer les procédures de règlement amiable des conflits du travail')
bul(doc, 'Création de dossiers de médiation liés à une plainte ou déclenchés directement')
bul(doc, '3 formats de séances : présentiel (convocation physique), en ligne (lien visioconférence), hybride')
bul(doc, 'Planification et envoi automatique des convocations aux parties (employeur + salarié + médiateur)')
bul(doc, 'Gestion du calendrier du médiateur avec disponibilités et réservations')
bul(doc, '4 types de résultats : Accord total, Accord partiel, Désaccord constaté, En attente')
bul(doc, 'Génération automatique du procès-verbal de conciliation (PDF) avec signature électronique')
bul(doc, 'Archivage des accords dans la GED avec indexation par entreprise, plaignant et type de litige')
bul(doc, 'Indicateurs : taux de médiation réussie, délai moyen de résolution, taux d\'accord par type de litige')

# ── Module 7 ─────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 7  –  Procédures Judiciaires', bg='00347C')
h2(doc, 'Objectif : Assurer le suivi des dossiers transmis à la justice du travail')
bul(doc, 'Création de procédures judiciaires avec numérotation : PROC-CI-AAAA-XXXXXX')
bul(doc, '7 types d\'affaires : litiges contractuels, licenciement abusif, discrimination, harcèlement, salaires, accidents du travail, droits syndicaux')
bul(doc, 'Cycle complet sur 8 statuts : Préparation → Déposé → En examen → Audience programmée → En attente de décision → Décision rendue → Appel → Clôturé')
bul(doc, 'Gestion des audiences : date, heure, lieu, juge, parties présentes, observations')
bul(doc, 'Interface avec le Tribunal du Travail d\'Abidjan et les tribunaux de travail régionaux')
bul(doc, 'Stockage sécurisé de toutes les pièces judiciaires : mémoires, conclusions, décisions')
bul(doc, 'Alertes sur les délais procéduraux (prescription, délais légaux d\'appel)')

# ── Module 8 ─────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 8  –  Travailleurs Domestiques', bg='006BAF')
h2(doc, 'Objectif : Formaliser et protéger le secteur du travail domestique (400K+ personnes en CI)')
bul(doc, '9 catégories : employés de maison, cuisiniers, nourrices/gardes d\'enfants, chauffeurs, jardiniers, agents de sécurité, aides-soignants, baby-sitters, personnel polyvalent')
bul(doc, 'Profil complet : identité, photo, CV numérique, certifications, expériences, références')
bul(doc, 'Enregistrement du contrat de travail domestique conforme au Décret 2017-552')
bul(doc, 'Carte professionnelle numérique avec QR code vérifiable par l\'inspecteur sur le terrain')
bul(doc, 'Suivi des entrées et sorties de service (check-in / check-out) pour les agences de placement')
bul(doc, 'Gestion des langues parlées (Français, Dioula, Baoulé, Bété, autres langues ivoiriennes)')
bul(doc, 'Module de mise en relation entre travailleurs disponibles et familles employeurs (optionnel)')

# ── Module 9 ─────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 9  –  Intelligence Artificielle et Analyse Documentaire', bg='00347C')
h2(doc, 'Objectif : Augmenter la productivité des agents et améliorer l\'accès au droit')
bul(doc, 'Chatbot juridique en Français : répond aux questions des travailleurs sur leurs droits (licenciement, contrat, congés, salaire minimum, etc.) en s\'appuyant sur le Code du Travail ivoirien')
bul(doc, 'Analyse automatique des documents : extraction des informations clés d\'un contrat de travail, d\'un bulletin de paie, d\'un bilan social')
bul(doc, 'OCR avancé (Reconnaissance Optique de Caractères) pour numériser les documents papier remis par les plaignants')
bul(doc, 'Transcription audio multilingue via OpenAI Whisper : Français, Dioula, Baoulé, Attié — utile pour les témoignages oraux des travailleurs peu alphabétisés')
bul(doc, 'Suggestion de qualification juridique des faits rapportés dans la plainte (aide à l\'inspecteur)')
bul(doc, 'Détection d\'anomalies : signalement automatique de bulletins de paie incohérents ou de contrats non conformes')
bul(doc, 'Résumés automatiques de dossiers complexes pour les rapports hiérarchiques')

# ── Module 10 ────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 10  –  Observatoire des Statistiques Sociales', bg='006BAF')
h2(doc, 'Objectif : Produire des données fiables pour la politique sociale et les rapports OIT')
bul(doc, 'Tableau de bord DG : vue nationale en temps réel — plaintes reçues, résolues, en cours, escaladées')
bul(doc, 'Statistiques quotidiennes automatisées : nombre de plaintes, taux de résolution, délai moyen')
bul(doc, 'Rapports mensuels et annuels générés automatiquement au format PDF et Excel')
bul(doc, 'Cartographie des risques sociaux par région, secteur d\'activité et type d\'infraction')
bul(doc, 'Taux de médiation réussie, taux de récidive des entreprises en infraction, taux d\'accidents du travail')
bul(doc, 'Comparatifs annuels et analyse des tendances sur 5 ans')
bul(doc, 'Exportation vers les systèmes de reporting OIT (ILOSTAT) et vers les portails open data gouvernementaux')
bul(doc, 'Alertes automatiques sur les indicateurs hors normes (hausse soudaine des plaintes dans un secteur, etc.)')

# ── Module 11 ────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 11  –  Business Intelligence et Tableaux de Bord', bg='00347C')
h2(doc, 'Objectif : Offrir des outils de pilotage personnalisés à chaque niveau hiérarchique')
bul(doc, 'Tableaux de bord modulaires configurables (widgets glisser-déposer) pour chaque profil')
bul(doc, '4 types de visualisations : tableaux de données, graphiques (barres, courbes, camembert, radar), tableaux croisés dynamiques, cartes choroplèthes')
bul(doc, 'Filtres dynamiques : période, région, type de plainte, secteur d\'activité, inspecteur')
bul(doc, 'Partage de rapports entre utilisateurs avec contrôle des droits de lecture/écriture')
bul(doc, 'Rapports planifiés : envoi automatique par e-mail à une liste de destinataires (ex : rapport hebdomadaire pour le DG)')
bul(doc, 'Export en PDF, Excel (.xlsx), CSV et PNG (pour les graphiques)')

# ── Module 12 ────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 12  –  GED – Gestion Électronique des Documents', bg='006BAF')
h2(doc, 'Objectif : Dématérialiser et sécuriser l\'archivage de tous les actes administratifs')
bul(doc, 'Arborescence documentaire hiérarchique (catégories, sous-catégories) avec politiques de rétention configurables')
bul(doc, 'Cycle de vie complet : Brouillon → Actif → Archivé → Supprimé (avec corbeille et restauration)')
bul(doc, 'Versionnage intégral : chaque modification crée une nouvelle version, l\'historique complet est conservé')
bul(doc, 'Contrôle d\'accès granulaire par document : lecture seule, modification, téléchargement, partage')
bul(doc, 'Piste d\'audit exhaustive : qui a consulté, téléchargé, modifié ou supprimé chaque document, avec horodatage')
bul(doc, 'Recherche plein texte dans les métadonnées des documents')
bul(doc, 'Organisation automatique par date : ged/documents/AAAA/MM/')
bul(doc, 'Conformité aux standards ISO 15489 (Records Management) et NF Z42-013 (archivage numérique)')

# ── Module 13 ────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 13  –  Notifications Multi-canaux', bg='00347C')
h2(doc, 'Objectif : Tenir informés tous les acteurs en temps réel et de manière proactive')
bul(doc, 'E-mail : modèles HTML/texte personnalisés par type d\'événement (plainte reçue, dossier assigné, médiation programmée, décision rendue)')
bul(doc, 'SMS : notifications critiques pour les plaignants sans accès internet, via opérateurs ivoiriens (Orange CI, MTN CI, Moov Africa)')
bul(doc, 'Notifications in-app en temps réel via WebSocket (Django Channels) — pastille rouge sur l\'interface')
bul(doc, 'Push notifications mobiles (iOS et Android) pour l\'application mobile')
bul(doc, 'Préférences de notification personnalisables par utilisateur (désactivation canal par canal)')
bul(doc, 'Historique complet des notifications envoyées avec statut de livraison')
bul(doc, 'Alerte hiérarchique automatique en cas de dépassement de délai')

# ── Module 14 ────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 14  –  Portail Public et Page d\'Accueil', bg='006BAF')
h2(doc, 'Objectif : Offrir une vitrine institutionnelle et un point d\'entrée citoyen')
bul(doc, 'Site web public de la DGT : actualités, annonces, communiqués de presse')
bul(doc, 'FAQ dynamique par catégorie : droit des salariés, obligations des employeurs, procédures de plainte')
bul(doc, 'Annuaire des directions régionales et locales avec coordonnées, horaires et carte')
bul(doc, 'Accès aux textes réglementaires : Code du Travail ivoirien, conventions collectives, décrets d\'application')
bul(doc, 'Formulaire de dépôt de plainte en ligne avec suivi par numéro de référence')
bul(doc, 'Accessibilité : responsive design (mobile-first), conforme WCAG 2.1 (niveau AA), optimisé pour les connexions lentes')
bul(doc, 'SEO optimisé pour la visibilité dans les moteurs de recherche')

# ── Module 15 ────────────────────────────────────────────════════════════════
banner(doc, 'MODULE 15  –  Administration Système et Audit', bg='00347C')
h2(doc, 'Objectif : Garantir la sécurité, la conformité et la maîtrise technique de la plateforme')
bul(doc, 'Console d\'administration dédiée pour la gestion des utilisateurs, des droits et des configurations')
bul(doc, 'Journal d\'audit complet et immuable : toutes les actions (création, modification, suppression, consultation de dossiers sensibles) sont enregistrées avec identité de l\'agent, horodatage et adresse IP')
bul(doc, 'Surveillance en temps réel des performances (temps de réponse API, charge serveur, erreurs)')
bul(doc, 'Gestion des configurations système avec chiffrement des paramètres sensibles (clés API, mots de passe)')
bul(doc, 'Outils de purge et d\'archivage conformes aux politiques de rétention de données')
bul(doc, 'Rapports d\'audit exportables pour les inspections et certifications de sécurité')

# ── Module 16 ────────────────────────────────────────────────────────────────
banner(doc, 'MODULE 16  –  Application Mobile (iOS et Android)', bg='006BAF')
h2(doc, 'Objectif : Étendre la plateforme aux usages terrain et aux zones peu connectées')
bul(doc, 'Application React Native disponible sur App Store (iOS) et Google Play (Android)')
bul(doc, 'Fonctionnement hors-ligne partiel (PWA) : consultation de dossiers, saisie de rapports d\'inspection, synchronisation automatique à la reconnexion')
bul(doc, 'Scan QR Code d\'une entreprise pour accéder instantanément à son dossier')
bul(doc, 'Géolocalisation de l\'inspecteur et de l\'entreprise visitée pour validation de présence')
bul(doc, 'Prise de photo et enregistrement audio directement intégrés au rapport d\'inspection')
bul(doc, 'Push notifications pour les alertes et assignations')
bul(doc, 'Interface simplifiée pour les travailleurs : dépôt de plainte en 5 étapes, suivi de dossier')
bul(doc, 'Support multilingue : Français (interface principale), avec assistance vocale Dioula et Baoulé (via IA)')

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 6. ARCHITECTURE TECHNIQUE ET SÉCURITÉ
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '6.  ARCHITECTURE TECHNIQUE ET SÉCURITÉ', sb=0)
add_hr(doc)

body(doc,
    'La plateforme est construite selon une architecture en microservices découplés, '
    'déployable sur infrastructure cloud ou on-premise au sein des datacenters du gouvernement '
    'ivoirien (CIE-Datacenter, Infrastructure nationale SI). Elle garantit scalabilité, '
    'haute disponibilité et sécurité de niveau institutionnel.')

h2(doc, '6.1  Pile technologique complète')
tech_data = [
    ('Couche',                'Technologie',                          'Version',   'Rôle'),
    ('Framework Backend',     'Django',                               '5.0.6',     'Logique métier, ORM, administration'),
    ('API REST',              'Django REST Framework',                '3.15.1',    'Endpoints API sécurisés et documentés'),
    ('Base de données',       'MySQL / MariaDB',                      '8.0+',      'Stockage relationnel principal'),
    ('Authentification',      'JWT + Simple JWT + PyOTP',             '5.3.1',     'Accès sécurisé + 2FA TOTP'),
    ('Tâches asynchrones',    'Celery + Redis',                       '5.3 / 5.0', 'Emails, notifications, calculs stats'),
    ('Temps réel',            'Django Channels + WebSocket',          '4.1.0',     'Notifications instantanées'),
    ('Stockage fichiers',     'AWS S3 / MinIO (on-premise)',          '',          'Documents, médias, sauvegardes'),
    ('IA / NLP',              'OpenAI GPT-4o + Whisper',              '',          'Chatbot juridique, OCR, transcription'),
    ('Documentation API',     'drf-spectacular (Swagger/ReDoc)',      '',          'Documentation interactive'),
    ('Frontend Web',          'React.js / TypeScript',                '',          'Interface utilisateur responsive'),
    ('Application Mobile',    'React Native (Expo)',                  '',          'iOS + Android'),
    ('Envoi Email',           'SMTP (Gmail/Office 365) + SendGrid',   '',          'Notifications, alertes'),
    ('Envoi SMS',             'Orange CI API / CinetPay SMS',         '',          'Alertes SMS aux travailleurs'),
    ('Monitoring',            'Prometheus + Grafana / Sentry',        '',          'Performance, erreurs, alertes ops'),
    ('CI/CD',                 'GitHub Actions / GitLab CI',           '',          'Déploiement automatisé, tests'),
]
t_tech = doc.add_table(rows=len(tech_data), cols=4)
t_tech.style = 'Table Grid'
t_tech.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(tech_data):
    row = t_tech.rows[i]
    bg = '00347C' if i == 0 else ('F5F7FA' if i % 2 == 0 else 'FFFFFF')
    tc = BLANC if i == 0 else GRIS_TEXTE
    for j, txt in enumerate(row_data):
        c = row.cells[j]
        cell_bg(c, bg)
        c.paragraphs[0].paragraph_format.space_before = Pt(4)
        c.paragraphs[0].paragraph_format.space_after  = Pt(4)
        r = c.paragraphs[0].add_run(txt)
        r.bold = (i == 0 or j == 0)
        r.font.size = Pt(9); r.font.color.rgb = tc; r.font.name = 'Calibri'

h2(doc, '6.2  Sécurité multi-couches')
secu_items = [
    ('Transport',       'TLS 1.3 obligatoire pour toutes les communications — aucune donnée en clair sur le réseau'),
    ('Authentification','JWT avec rotation des tokens + OTP à 6 chiffres (TOTP) obligatoire pour les agents DGT'),
    ('Chiffrement',     'Données sensibles chiffrées au repos avec AES-256 (configurations, tokens, données médicales)'),
    ('Autorisation',    'RBAC granulaire : chaque action est vérifiée contre les droits de l\'utilisateur connecté'),
    ('Audit',           'Journal d\'audit immuable en base de données avec signature numérique des entrées critiques'),
    ('Sauvegardes',     'Sauvegardes automatiques quotidiennes, chiffrées, stockées hors site — rétention 30 jours'),
    ('RGPD / PDCI',     'Conformité à la loi ivoirienne n° 2013-450 sur la protection des données personnelles (ARTCI)'),
    ('Tests sécurité',  'Test de pénétration (pentest) externe avant mise en production + analyse statique du code'),
    ('WAF',             'Pare-feu applicatif web (WAF) et protection DDoS sur l\'infrastructure cloud'),
]
t_secu = doc.add_table(rows=len(secu_items) + 1, cols=2)
t_secu.style = 'Table Grid'
t_secu.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl_header_row(t_secu.rows[0], ['Couche de sécurité', 'Mesure mise en œuvre'])
for i, (couche, mesure) in enumerate(secu_items, 1):
    bg = 'F5F7FA' if i % 2 == 0 else 'FFFFFF'
    tbl_data_cell(t_secu.rows[i].cells[0], couche,  bg=bg, txt_color=BLEU_FONCE, bold=True)
    tbl_data_cell(t_secu.rows[i].cells[1], mesure,  bg=bg)

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 7. PLAN DE DÉPLOIEMENT
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '7.  PLAN DE DÉPLOIEMENT (4 PHASES – 18 MOIS)', sb=0)
add_hr(doc)

body(doc,
    'Le déploiement est organisé en quatre phases progressives permettant une montée en puissance '
    'contrôlée, une réduction des risques et une adoption durable par les équipes de la DGT. '
    'Chaque phase fait l\'objet d\'un Procès-Verbal de Réception signé conjointement.')

phases = [
    {
        'num': 'PHASE 1', 'titre': 'Cadrage, Configuration et Migration (Mois 1–3)',
        'bg': '00347C',
        'livrables': [
            'Atelier de lancement avec la DGT : validation du périmètre fonctionnel, cartographie des processus existants, identification des parties prenantes',
            'Installation et configuration de l\'environnement de recette (UAT) et de production',
            'Paramétrage du référentiel métier : 19 directions régionales, zones d\'inspection, types de plaintes, rôles et droits',
            'Migration de l\'annuaire des agents DGT existants (import sécurisé depuis fichiers Excel)',
            'Import du registre des entreprises existant (RCCM/CNPS) avec dédoublonnage',
            'Déploiement de l\'infrastructure cloud (hébergement, DNS, certificats SSL)',
            'Formation de l\'équipe IT du Ministère sur l\'administration système',
            'PV de réception de la Phase 1',
        ]
    },
    {
        'num': 'PHASE 2', 'titre': 'Pilote Abidjan-Plateau et Districts (Mois 4–7)',
        'bg': '005A99',
        'livrables': [
            'Mise en production sur le périmètre Abidjan-Plateau, Cocody, Marcory, Yopougon',
            'Formation des 40 premiers inspecteurs (présentiel – 3 jours par groupe de 20)',
            'Formation des agents du guichet de réception des plaintes',
            'Activation du portail citoyen pour le dépôt de plaintes en ligne',
            'Support renforcé sur site (1 ingénieur Numerix Digital en résidence à la DGT)',
            'Collecte systématique des retours utilisateurs avec formulaire de feedback',
            'Ajustements fonctionnels et corrections d\'anomalies (sprint bi-hebdomadaire)',
            'Premier rapport de performance pilote à 30 jours et à 90 jours',
            'PV de réception de la Phase 2',
        ]
    },
    {
        'num': 'PHASE 3', 'titre': 'Déploiement National (Mois 8–14)',
        'bg': '009A44',
        'livrables': [
            'Extension à toutes les 19 directions régionales : Bouaké, Yamoussoukro, Daloa, San-Pédro, Korhogo, Man, Abengourou, Divo, Gagnoa, Bondoukou, Dimbokro, Odienné, Guiglo, Lakota, Soubré, Sassandra, Agboville, Adzopé, Aboisso',
            'Formation de 360 agents supplémentaires (inspecteurs, chefs, directeurs régionaux)',
            'Activation des modules avancés : IA/chatbot, observatoire statistique, GED complète',
            'Lancement du module Travailleurs Domestiques avec campagne de communication',
            'Interconnexion avec le système CNPS (Caisse Nationale de Prévoyance Sociale)',
            'Mise en place du tableau de bord national du DG et des directeurs régionaux',
            'Activation des alertes SMS via opérateurs ivoiriens',
            'Atelier de présentation des premiers résultats à la hiérarchie du Ministère',
            'PV de réception de la Phase 3',
        ]
    },
    {
        'num': 'PHASE 4', 'titre': 'Consolidation et Transfert de Compétences (Mois 15–18)',
        'bg': 'F47E1C',
        'livrables': [
            'Audit de performance technique et fonctionnelle',
            'Optimisations basées sur les données d\'usage (6 mois de production)',
            'Production du premier Rapport Annuel Numérique de l\'Inspection du Travail de Côte d\'Ivoire',
            'Transfert de compétences complet : formation des développeurs IT du Ministère sur le code source',
            'Documentation technique complète : architecture, APIs, modèle de données',
            'Mise en place du contrat de maintenance et du SLA post-déploiement',
            'Présentation du bilan et de la roadmap des évolutions futures au Directeur Général',
            'PV de Réception Définitive signé par la DGT et Numerix Digital',
        ]
    },
]

for ph in phases:
    banner(doc, f"{ph['num']}  –  {ph['titre']}", bg=ph['bg'])
    doc.add_paragraph()
    for liv in ph['livrables']:
        bul(doc, liv)
    doc.add_paragraph()

h2(doc, '7.1  Chronogramme synthétique')
chron_data = [
    ('Livrable / Jalon',                          'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8-10', 'M11-14', 'M15-18'),
    ('Cadrage et paramétrage',                    '●', '●', '',   '',   '',   '',   '',   '',      '',       ''),
    ('Migration données existantes',              '',  '●', '●', '',   '',   '',   '',   '',      '',       ''),
    ('Infrastructure cloud',                      '●', '●', '',   '',   '',   '',   '',   '',      '',       ''),
    ('Pilote Abidjan',                            '',  '',  '●', '●', '●', '●', '',   '',      '',       ''),
    ('Formation 1ère vague',                      '',  '',  '●', '●', '',   '',   '',   '',      '',       ''),
    ('Déploiement national',                      '',  '',  '',   '',   '',  '●', '●', '●',    '',       ''),
    ('Formation 2ème vague',                      '',  '',  '',   '',   '',   '',  '●', '●',    '',       ''),
    ('Modules avancés (IA, GED, Observatoire)',   '',  '',  '',   '',   '',   '',   '',  '●',   '●',      ''),
    ('Interconnexion CNPS',                       '',  '',  '',   '',   '',   '',   '',   '',     '●',      ''),
    ('Optimisation et transfert compétences',     '',  '',  '',   '',   '',   '',   '',   '',     '',       '●'),
    ('Rapport annuel et réception définitive',    '',  '',  '',   '',   '',   '',   '',   '',     '',       '●'),
]
t_chron = doc.add_table(rows=len(chron_data), cols=11)
t_chron.style = 'Table Grid'
t_chron.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(chron_data):
    row = t_chron.rows[i]
    is_h = (i == 0)
    for j, txt in enumerate(row_data):
        c = row.cells[j]
        bg = '00347C' if is_h else ('F5F7FA' if i % 2 == 0 else 'FFFFFF')
        if not is_h and txt == '●':
            bg = 'B8D8FF'
        cell_bg(c, bg)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER if j > 0 else WD_ALIGN_PARAGRAPH.LEFT
        c.paragraphs[0].paragraph_format.space_before = Pt(4)
        c.paragraphs[0].paragraph_format.space_after  = Pt(4)
        r = c.paragraphs[0].add_run(txt)
        r.bold = is_h or (txt == '●')
        r.font.size = Pt(8.5)
        r.font.color.rgb = BLANC if is_h else (BLEU_FONCE if txt == '●' else GRIS_TEXTE)
        r.font.name = 'Calibri'

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 8. FORMATION ET ACCOMPAGNEMENT
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '8.  FORMATION ET ACCOMPAGNEMENT AU CHANGEMENT', sb=0)
add_hr(doc)

body(doc,
    'Le succès d\'un projet de transformation numérique repose à 30 % sur la technologie et '
    'à 70 % sur l\'humain. Numerix Digital place la formation et l\'accompagnement au changement '
    'au cœur de sa démarche de déploiement.')

h2(doc, '8.1  Catalogue de formations')
formations = [
    ('F01', 'Administration système',        '2 jours',  '10 admins IT',      'Gestion utilisateurs, sauvegardes, monitoring, incidents'),
    ('F02', 'Inspecteurs du travail',        '3 jours',  '120/session',       'Saisie rapports, gestion plaintes, app mobile, signatures électroniques'),
    ('F03', 'Chefs d\'inspection',           '2 jours',  '80 chefs',          'Validation, tableau de bord, statistiques d\'équipe'),
    ('F04', 'Directeurs régionaux',          '1 jour',   '19 directeurs',     'Pilotage régional, indicateurs, approbation de dossiers complexes'),
    ('F05', 'Direction Générale',            '0,5 jour', 'DG + staff DG',     'Observatoire national, tableaux de bord stratégiques, exports OIT'),
    ('F06', 'Agents guichet plaintes',       '1 jour',   '60 agents',         'Réception et saisie des plaintes, gestion des PJ, communication plaignant'),
    ('F07', 'Médiateurs/Conciliateurs',      '1 jour',   '50 médiateurs',     'Module médiation, planification séances, génération PV'),
    ('F08', 'Formation des formateurs',      '2 jours',  '20 formateurs',     'Former les futurs formateurs internes de la DGT (pérennisation)'),
]
t_form = doc.add_table(rows=len(formations) + 1, cols=5)
t_form.style = 'Table Grid'
t_form.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl_header_row(t_form.rows[0], ['Réf.', 'Cible', 'Durée', 'Effectif', 'Contenu principal'])
for i, row_data in enumerate(formations, 1):
    bg = 'F5F7FA' if i % 2 == 0 else 'FFFFFF'
    for j, txt in enumerate(row_data):
        tbl_data_cell(t_form.rows[i].cells[j], txt, bg=bg,
                      txt_color=BLEU_FONCE if j == 0 else GRIS_TEXTE,
                      bold=(j == 0))

h2(doc, '8.2  Supports livrés')
bul(doc, 'Guide utilisateur illustré par profil (8 guides distincts, format PDF et web)')
bul(doc, 'Vidéos tutorielles pour les 5 fonctions principales (sous-titrées en Français)')
bul(doc, 'FAQ interactive accessible depuis la plateforme (mise à jour continue)')
bul(doc, 'Hotline dédiée pendant les 6 premiers mois post-déploiement')
bul(doc, 'Webinaires mensuels de suivi pendant 12 mois')

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 9. OFFRE FINANCIÈRE DÉTAILLÉE
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '9.  OFFRE FINANCIÈRE DÉTAILLÉE', sb=0)
add_hr(doc)

body(doc,
    'L\'offre financière se compose d\'un investissement initial couvrant la mise en œuvre '
    'complète sur 18 mois (licence, déploiement, formation, accompagnement, infrastructure), '
    'suivi d\'un abonnement annuel de maintenance et d\'exploitation. Tous les prix sont '
    'exprimés en Francs CFA (FCFA), hors taxes.')

h2(doc, '9.1  Détail de l\'investissement initial (18 mois)')

inv_data = [
    ('Réf.',     'Prestation',                                                     'Unité',   'Qté', 'P.U. HT (FCFA)',  'Total HT (FCFA)'),
    ('LOT-01',   'Licence logicielle perpétuelle – Plateforme e-Inspection DGT CI', 'Forfait', '1',   '18 000 000',      '18 000 000'),
    ('LOT-02',   'Développement et personnalisation spécifique DGT-CI',             'Forfait', '1',   '10 000 000',      '10 000 000'),
    ('LOT-03',   'Intégration IA (chatbot juridique CI + OCR + transcription)',      'Forfait', '1',   '6 500 000',       '6 500 000'),
    ('LOT-04',   'Application mobile iOS et Android (React Native)',                 'Forfait', '1',   '7 000 000',       '7 000 000'),
    ('LOT-05',   'Déploiement et configuration infrastructure cloud',                'Forfait', '1',   '4 000 000',       '4 000 000'),
    ('LOT-06',   'Migration et import des données existantes (RCCM, CNPS, agents)', 'Forfait', '1',   '3 500 000',       '3 500 000'),
    ('LOT-07',   'Interconnexion CNPS (API temps réel)',                            'Forfait', '1',   '4 500 000',       '4 500 000'),
    ('LOT-08',   'Formation – F01 (Admins IT)',                                     'Session', '1',   '1 500 000',       '1 500 000'),
    ('LOT-09',   'Formation – F02 (Inspecteurs, 4 sessions × 3 jours)',             'Session', '4',   '1 800 000',       '7 200 000'),
    ('LOT-10',   'Formation – F03 à F08 (autres profils)',                          'Forfait', '1',   '4 500 000',       '4 500 000'),
    ('LOT-11',   'Accompagnement au changement (18 mois)',                          'Forfait', '1',   '5 000 000',       '5 000 000'),
    ('LOT-12',   'Hébergement cloud et bande passante (18 mois)',                   'Mois',    '18',  '600 000',         '10 800 000'),
    ('LOT-13',   'Tests de pénétration et audit de sécurité',                       'Forfait', '1',   '3 000 000',       '3 000 000'),
    ('LOT-14',   'Documentation technique complète et transfert de compétences IT', 'Forfait', '1',   '2 500 000',       '2 500 000'),
    ('',         'SOUS-TOTAL HORS TAXES',                                           '',        '',    '',                '88 000 000'),
    ('',         'TVA (18 %)',                                                       '',        '',    '',                '15 840 000'),
    ('',         'TOTAL INVESTISSEMENT TOUTES TAXES COMPRISES',                     '',        '',    '',               '103 840 000'),
]

t_inv = doc.add_table(rows=len(inv_data), cols=6)
t_inv.style = 'Table Grid'
t_inv.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(inv_data):
    row = t_inv.rows[i]
    is_h   = (i == 0)
    is_ttc = 'TOUTES TAXES COMPRISES' in row_data[1]
    is_sub = row_data[1].startswith('SOUS-TOTAL') or row_data[1].startswith('TVA')

    if is_h:
        bg, tc = '00347C', BLANC
    elif is_ttc:
        bg, tc = '00347C', BLANC
    elif is_sub:
        bg, tc = 'DCF0FF', BLEU_FONCE
    else:
        bg, tc = ('F5F7FA' if i % 2 == 0 else 'FFFFFF'), GRIS_TEXTE

    for j, txt in enumerate(row_data):
        c = row.cells[j]
        cell_bg(c, bg)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT if j >= 4 else WD_ALIGN_PARAGRAPH.LEFT
        c.paragraphs[0].paragraph_format.space_before = Pt(4)
        c.paragraphs[0].paragraph_format.space_after  = Pt(4)
        r = c.paragraphs[0].add_run(txt)
        r.bold = is_h or is_sub or is_ttc or j == 0
        r.font.size = Pt(9 if not is_ttc else 10)
        r.font.color.rgb = tc; r.font.name = 'Calibri'

doc.add_paragraph()

h2(doc, '9.2  Abonnement annuel de maintenance (à partir de l\'année 2)')
maint_data = [
    ('Prestation',                                               'Détail',                                              'Montant HT (FCFA)'),
    ('Maintenance corrective',                                   'Correction bugs et anomalies, patches sécurité',      '4 000 000'),
    ('Maintenance évolutive mineure',                            'Évolutions UI, nouveaux paramètres, améliorations',   '5 000 000'),
    ('Hébergement cloud (serveurs, BD, stockage, bande passante)','Infrastructure dédiée DGT',                          '7 200 000'),
    ('Licences tierces (OpenAI, SMS gateway)',                   'Consommation API IA + SMS (plafonné 50K SMS/an)',      '3 500 000'),
    ('Support utilisateurs (Hotline + tickets)',                  'L–V 8h–18h, délai réponse < 4h',                     '3 000 000'),
    ('Mises à jour de sécurité',                                 'Audits sécurité semestriels, pentest annuel',         '2 500 000'),
    ('Formations complémentaires (2 sessions/an)',               'Montée en compétences sur nouvelles fonctionnalités', '1 800 000'),
    ('TOTAL ANNUEL HT',                                          '',                                                    '27 000 000'),
    ('TVA (18 %)',                                               '',                                                    '4 860 000'),
    ('TOTAL ANNUEL TTC',                                         '',                                                    '31 860 000'),
]
t_maint = doc.add_table(rows=len(maint_data), cols=3)
t_maint.style = 'Table Grid'
t_maint.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(maint_data):
    row = t_maint.rows[i]
    is_ttc = 'TTC' in row_data[0]
    is_tot = 'TOTAL' in row_data[0]
    bg = ('00347C' if is_ttc else ('DCF0FF' if is_tot else ('F5F7FA' if i % 2 == 0 else 'FFFFFF')))
    tc = (BLANC if is_ttc else (BLEU_FONCE if is_tot else GRIS_TEXTE))
    for j, txt in enumerate(row_data):
        c = row.cells[j]
        cell_bg(c, bg)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT if j == 2 else WD_ALIGN_PARAGRAPH.LEFT
        c.paragraphs[0].paragraph_format.space_before = Pt(5)
        c.paragraphs[0].paragraph_format.space_after  = Pt(5)
        r = c.paragraphs[0].add_run(txt)
        r.bold = is_tot or is_ttc; r.font.size = Pt(9.5)
        r.font.color.rgb = tc; r.font.name = 'Calibri'

doc.add_paragraph()

h2(doc, '9.3  Récapitulatif financier global (5 ans)')
recap = [
    ('Période',                    'Montant TTC (FCFA)',   'Cumul TTC (FCFA)'),
    ('Investissement initial (An 1)', '103 840 000',       '103 840 000'),
    ('Maintenance An 2',              '31 860 000',        '135 700 000'),
    ('Maintenance An 3',              '31 860 000',        '167 560 000'),
    ('Maintenance An 4',              '31 860 000',        '199 420 000'),
    ('Maintenance An 5',              '31 860 000',        '231 280 000'),
    ('COÛT TOTAL SUR 5 ANS (TTC)',    '231 280 000',       '–'),
]
t_recap = doc.add_table(rows=len(recap), cols=3)
t_recap.style = 'Table Grid'
t_recap.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(recap):
    row = t_recap.rows[i]
    is_h = (i == 0)
    is_tot = 'COÛT TOTAL' in row_data[0]
    bg = ('00347C' if is_h else ('F47E1C' if is_tot else ('F5F7FA' if i % 2 == 0 else 'FFFFFF')))
    tc = BLANC if (is_h or is_tot) else GRIS_TEXTE
    for j, txt in enumerate(row_data):
        c = row.cells[j]
        cell_bg(c, bg)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT if j > 0 else WD_ALIGN_PARAGRAPH.LEFT
        c.paragraphs[0].paragraph_format.space_before = Pt(5)
        c.paragraphs[0].paragraph_format.space_after  = Pt(5)
        r = c.paragraphs[0].add_run(txt)
        r.bold = is_h or is_tot; r.font.size = Pt(10)
        r.font.color.rgb = tc; r.font.name = 'Calibri'

h2(doc, '9.4  Modalités de paiement')
bul(doc, '30 % à la signature du contrat : 31 152 000 FCFA TTC — déclenchement des travaux')
bul(doc, '30 % à la Réception de la Phase 2 (pilote Abidjan validé) : 31 152 000 FCFA TTC')
bul(doc, '25 % à la Réception de la Phase 3 (déploiement national validé) : 25 960 000 FCFA TTC')
bul(doc, '15 % à la Réception Définitive (Phase 4 – rapport annuel livré) : 15 576 000 FCFA TTC')
body(doc,
    'Paiement par virement bancaire. Devise : Franc CFA XOF. TVA applicable : 18 %. '
    'Les prix sont fermes et non révisables pendant toute la durée du projet. '
    'Validité de l\'offre : 90 jours à compter du ' + TODAY.strftime('%d %B %Y') + '.',
    italic=True, color=GRIS_MOYEN)

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 10. NIVEAUX DE SERVICE (SLA)
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '10.  NIVEAUX DE SERVICE (SLA)', sb=0)
add_hr(doc)

sla_data = [
    ('Indicateur de service',                        'Engagement contractuel',               'Pénalité si non-respect'),
    ('Disponibilité de la plateforme',               '99,5 % / mois (hors maintenances)',   'Crédit d\'1 mois de maintenance'),
    ('Temps de réponse – Page web',                  '< 2 secondes (95e percentile)',        'Rapport d\'incident dans 48h'),
    ('Temps de réponse – API',                       '< 500ms (95e percentile)',              'Rapport d\'incident dans 48h'),
    ('Incident CRITIQUE (plateforme down)',          'Prise en charge < 1h, résolution < 4h', 'Crédit proportionnel'),
    ('Incident MAJEUR (module bloqué)',              'Prise en charge < 4h, résolution < 8h', 'Rapport d\'analyse'),
    ('Incident MINEUR (bug non bloquant)',           'Résolution dans les 3 jours ouvrés',   'Suivi hebdomadaire'),
    ('Sauvegarde des données',                       'Quotidienne – Rétention 30 jours',     'Audit immédiat'),
    ('Restauration des données (RTO)',               '< 4 heures (objectif 2h)',              'Test annuel documenté'),
    ('Perte de données maximale (RPO)',               '< 24 heures (objectif 1h)',             'Test semestriel'),
    ('Maintenance planifiée',                         'Dimanche 01h–05h (GMT)',               'Préavis 72h par e-mail'),
    ('Support téléphonique',                          'Lundi–Vendredi, 7h30–17h30 (GMT)',     'Ticket ouvert < 30min'),
    ('Rapport mensuel de disponibilité',              '5 du mois M+1',                        'Envoi automatique'),
    ('Mise à jour de sécurité critique',              'Déployée dans les 48h',                'Notification immédiate DGT-IT'),
]
t_sla = doc.add_table(rows=len(sla_data), cols=3)
t_sla.style = 'Table Grid'
t_sla.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(sla_data):
    row = t_sla.rows[i]
    is_h = (i == 0)
    bg = '00347C' if is_h else ('F5F7FA' if i % 2 == 0 else 'FFFFFF')
    tc = BLANC if is_h else GRIS_TEXTE
    for j, txt in enumerate(row_data):
        c = row.cells[j]
        cell_bg(c, bg)
        c.paragraphs[0].paragraph_format.space_before = Pt(5)
        c.paragraphs[0].paragraph_format.space_after  = Pt(5)
        r = c.paragraphs[0].add_run(txt)
        r.bold = is_h or j == 0; r.font.size = Pt(9.5 if not is_h else 9)
        r.font.color.rgb = (tc if not (not is_h and j == 0) else BLEU_FONCE); r.font.name = 'Calibri'

body(doc,
    'Une période de garantie de 12 mois est incluse dans le prix de mise en œuvre. Durant cette '
    'période, toutes les corrections liées au périmètre contractuel sont prises en charge sans surcoût. '
    'Un comité de pilotage mensuel réunit les représentants de la DGT et de Numerix Digital pour '
    'le suivi des indicateurs de service.',
    sb=10)

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 11. NOTRE ENTREPRISE ET ÉQUIPE PROJET
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '11.  NOTRE ENTREPRISE ET ÉQUIPE PROJET', sb=0)
add_hr(doc)

h2(doc, '11.1  Numerix Digital – Présentation')
body(doc,
    'Numerix Digital est une entreprise de développement logiciel et de conseil en transformation '
    'numérique spécialisée dans les solutions e-gouvernement pour l\'Afrique subsaharienne. '
    'Notre équipe de 25 ingénieurs et consultants conçoit et déploie des plateformes digitales '
    'sur mesure pour les administrations publiques, les établissements financiers et les grandes '
    'entreprises d\'Afrique centrale et occidentale.')

h2(doc, '11.2  Nos différenciateurs')
diff = [
    ('Expertise e-gouvernement', 'Plusieurs plateformes de gestion administrative déployées avec succès pour des ministères et organismes publics en Afrique centrale. Maîtrise des contraintes réglementaires, des procédures de marchés publics et des exigences de gouvernance du secteur public.'),
    ('Technologie de pointe', 'Stack technique moderne (Django, React, React Native, Redis, Celery, IA/LLM) permettant des déploiements rapides, sécurisés et maintenables. Pratiques DevOps (CI/CD, tests automatisés, infrastructure as code) pour une qualité maîtrisée.'),
    ('Engagement transfert de compétences', 'Nous ne livrons pas seulement un logiciel : nous formons les équipes, documentons l\'architecture et accompagnons la montée en autonomie des équipes IT du Ministère. La dépendance vis-à-vis du prestataire décroît dans le temps.'),
    ('Support local pérenne', 'Présence locale, réactivité en fuseau horaire GMT pour le support, capacité à mobiliser une équipe sur site si nécessaire. Nous parlons le même contexte réglementaire et culturel que nos clients africains.'),
    ('Engagement RSE', 'Engagement à recruter et former des développeurs locaux ivoiriens sur le projet, contribuant au renforcement de l\'écosystème numérique national.'),
]
for titre, desc in diff:
    h3(doc, f'▶  {titre}')
    body(doc, desc)

h2(doc, '11.3  Équipe projet dédiée')
eq_data = [
    ('Rôle',                         'Expérience',       'Temps alloué', 'Responsabilités clés'),
    ('Chef de projet',               '10 ans',           '100 %',        'Pilotage, coordination DGT, reporting, gestion des risques'),
    ('Architecte technique senior',  '12 ans',           '60 %',         'Architecture système, sécurité, choix technologiques, revue de code'),
    ('Lead développeur Backend',     '8 ans',            '100 %',        'API Django, base de données, intégrations CNPS/CNSS'),
    ('Développeur Backend #2',       '5 ans',            '100 %',        'Modules métier, tests unitaires, performances'),
    ('Lead développeur Frontend',    '7 ans',            '100 %',        'Interface web React/TypeScript, UX, accessibilité'),
    ('Développeur Mobile',           '5 ans',            '100 %',        'Application React Native iOS/Android'),
    ('Expert IA / Data Science',     '6 ans',            '60 %',         'Chatbot juridique, OCR, observatoire, ML'),
    ('Ingénieur DevOps / Sécurité',  '7 ans',            '60 %',         'Infrastructure cloud, CI/CD, monitoring, audit sécurité'),
    ('Spécialiste Formation',        '8 ans',            '80 %',         'Formation agents DGT, guides utilisateurs, accompagnement changement'),
    ('Ingénieur support (post-prod)','4 ans',            '100 %',        'Helpdesk, maintenance, tickets, monitoring quotidien'),
]
t_eq = doc.add_table(rows=len(eq_data), cols=4)
t_eq.style = 'Table Grid'
t_eq.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(eq_data):
    row = t_eq.rows[i]
    is_h = (i == 0)
    bg = '00347C' if is_h else ('F5F7FA' if i % 2 == 0 else 'FFFFFF')
    tc = BLANC if is_h else GRIS_TEXTE
    for j, txt in enumerate(row_data):
        c = row.cells[j]
        cell_bg(c, bg)
        c.paragraphs[0].paragraph_format.space_before = Pt(5)
        c.paragraphs[0].paragraph_format.space_after  = Pt(5)
        r = c.paragraphs[0].add_run(txt)
        r.bold = is_h or j == 0; r.font.size = Pt(9)
        r.font.color.rgb = tc; r.font.name = 'Calibri'

h2(doc, '11.4  Références pertinentes')
refs = [
    ('Plateforme nationale de gestion de projets et courrier administratif', 'Administrations centrales — Gestion de 10 000+ documents et 500+ utilisateurs simultanés'),
    ('Système de diligences et GED électronique sécurisée', 'Secteur financier — Conformité UEMOA, audit trail complet, zéro incident de sécurité en 3 ans'),
    ('Plateforme e-commerce et paiement mobile (Orange Money / Wave)', 'Secteur commerce — 50 000+ transactions/mois, intégration CinetPay et Bizao'),
    ('Solution de gestion de la publicité digitale et affichage', 'Médias et communication — Campagne cross-supports, reporting temps réel'),
    ('Application mobile de terrain pour inspection qualité', 'Agro-industrie — Fonctionnement hors-ligne, sync GPS, 200+ inspecteurs mobiles'),
]
t_ref = doc.add_table(rows=len(refs) + 1, cols=2)
t_ref.style = 'Table Grid'
t_ref.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl_header_row(t_ref.rows[0], ['Projet', 'Contexte et résultats'])
for i, (proj, ctx) in enumerate(refs, 1):
    bg = 'F5F7FA' if i % 2 == 0 else 'FFFFFF'
    tbl_data_cell(t_ref.rows[i].cells[0], proj, bg=bg, txt_color=BLEU_FONCE, bold=True)
    tbl_data_cell(t_ref.rows[i].cells[1], ctx,  bg=bg)

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 12. PROPOSITION DE VALEUR DIFFÉRENCIANTE
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '12.  PROPOSITION DE VALEUR DIFFÉRENCIANTE', sb=0)
add_hr(doc)

body(doc,
    'Pourquoi choisir Numerix Digital et la Plateforme e-Inspection du Travail '
    'plutôt qu\'une solution générique ou un développement interne ?')

diff_val = [
    ('Conçu pour la Côte d\'Ivoire',
     'La solution intègre nativement le Code du Travail ivoirien (Loi 2015-532), les conventions '
     'collectives nationales, les 19 directions régionales du travail, les opérateurs SMS locaux '
     '(Orange CI, MTN CI, Moov Africa) et le contexte linguistique national (Dioula, Baoulé, Attié). '
     'Ce n\'est pas une solution étrangère adaptée : c\'est une solution pensée pour la Côte d\'Ivoire.'),
    ('Solution complète, non fragmentée',
     '16 modules intégrés dans une seule plateforme = une seule source de vérité, '
     'une seule interface utilisateur, un seul fournisseur à gérer, une seule piste d\'audit. '
     'Pas besoin d\'assembler et de maintenir plusieurs logiciels disparates.'),
    ('IA au service des agents DGT',
     'Le chatbot juridique réduit la charge des agents en répondant aux questions récurrentes '
     'des travailleurs 24h/24. L\'OCR et la transcription audio permettent de traiter plus '
     'rapidement des dossiers papier ou des témoignages oraux.'),
    ('Accessibilité sur mobile dans un contexte à forte pénétration smartphone',
     'La Côte d\'Ivoire compte plus de 20 millions d\'abonnés mobiles. L\'application mobile '
     'native (iOS/Android) + la conception mobile-first du portail web garantissent l\'accès '
     'au service depuis n\'importe quel smartphone, même en connexion 3G.'),
    ('Pérennité et autonomie',
     'Transfert de code source, formation des développeurs IT du Ministère, documentation '
     'architecture complète : la DGT devient progressivement autonome et n\'est pas '
     'dépendante à vie du prestataire pour les évolutions courantes.'),
    ('Retour sur investissement mesurable',
     '60 % de réduction des délais de traitement des plaintes, 100 % de traçabilité, '
     'réduction des coûts papier et de déplacement estimée à 15 millions FCFA/an, '
     'amélioration de l\'image institutionnelle de la DGT auprès des partenaires sociaux.'),
]
for titre, desc in diff_val:
    t_dv = doc.add_table(rows=1, cols=1)
    t_dv.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_dv = t_dv.rows[0].cells[0]
    cell_bg(c_dv, 'DCF0FF')
    c_dv.paragraphs[0].paragraph_format.space_before = Pt(8)
    c_dv.paragraphs[0].paragraph_format.space_after  = Pt(4)
    r_t = c_dv.paragraphs[0].add_run(f'✓  {titre}')
    r_t.bold = True; r_t.font.size = Pt(11)
    r_t.font.color.rgb = BLEU_FONCE; r_t.font.name = 'Calibri'
    p_d = c_dv.add_paragraph()
    p_d.paragraph_format.space_before = Pt(2)
    p_d.paragraph_format.space_after  = Pt(8)
    r_d = p_d.add_run(f'    {desc}')
    r_d.font.size = Pt(10); r_d.font.color.rgb = GRIS_TEXTE; r_d.font.name = 'Calibri'
    doc.add_paragraph()

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 13. CONDITIONS GÉNÉRALES ET JURIDIQUES
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '13.  CONDITIONS GÉNÉRALES ET JURIDIQUES', sb=0)
add_hr(doc)

cg = [
    ('Propriété intellectuelle',
     'La licence logicielle accordée à la Direction Générale du Travail est perpétuelle, '
     'non exclusive et non transférable. Le code source des développements spécifiques '
     'réalisés pour la DGT-CI peut être cédé en pleine propriété sur demande, dans les '
     'termes d\'un avenant au contrat principal.'),
    ('Confidentialité',
     'Numerix Digital s\'engage à maintenir la stricte confidentialité de toutes les '
     'informations, données, documents et accès mis à disposition dans le cadre du projet. '
     'Cet engagement s\'applique à l\'ensemble du personnel de Numerix Digital mobilisé '
     'sur le projet et est valable sans limitation de durée, y compris après la fin du contrat. '
     'Un accord de confidentialité (NDA) séparé peut être signé à la demande de la DGT.'),
    ('Protection des données personnelles',
     'La plateforme est conçue en conformité avec la Loi ivoirienne n° 2013-450 du 19 juin '
     '2013 relative à la protection des données à caractère personnel (ARTCI) et les '
     'recommandations du RGPD européen. Les données personnelles des travailleurs et employeurs '
     'ne seront jamais transmises à des tiers, ni utilisées à des fins commerciales. '
     'Un registre des traitements de données sera mis à disposition de la DGT.'),
    ('Hébergement et souveraineté des données',
     'Les données de la DGT seront hébergées sur des serveurs physiquement situés en Côte '
     'd\'Ivoire ou dans l\'UEMOA, à la demande du Ministère. Numerix Digital peut également '
     'déployer sur une infrastructure on-premise au sein des datacenters gouvernementaux.'),
    ('Force majeure',
     'Aucune des parties ne pourra être tenue responsable d\'un manquement à ses obligations '
     'contractuelles résultant d\'un événement de force majeure tel que défini par le droit '
     'ivoirien (catastrophe naturelle, émeutes, pandémie, interruption des réseaux nationaux).'),
    ('Droit applicable et juridiction',
     'Le présent contrat est régi par le droit de la République de Côte d\'Ivoire. '
     'Tout litige relatif à son interprétation ou son exécution sera soumis, à défaut '
     'd\'accord amiable dans un délai de 30 jours, à la juridiction compétente du Tribunal '
     'de Commerce d\'Abidjan, dont les parties font expressément élection de domicile.'),
    ('Sous-traitance',
     'Numerix Digital pourra faire appel à des sous-traitants spécialisés pour certaines '
     'prestations (hébergement cloud, sécurité, gateway SMS). La DGT en sera informée par '
     'écrit. La responsabilité contractuelle principale demeure celle de Numerix Digital.'),
    ('Modifications du contrat',
     'Toute modification du périmètre, des délais ou du budget fera l\'objet d\'un avenant '
     'signé par les deux parties avant mise en œuvre. Un comité de pilotage mensuel est '
     'mis en place pour piloter conjointement le projet et traiter les demandes d\'évolution.'),
    ('Résiliation',
     'Chaque partie peut résilier le contrat avec un préavis de 60 jours en cas de '
     'manquement grave non corrigé de l\'autre partie dans un délai de 30 jours après '
     'mise en demeure. Les livrables réalisés restent la propriété de la DGT, les '
     'sommes correspondantes aux livrables acceptés restent dues.'),
]
for titre, texte in cg:
    h2(doc, titre, sb=8)
    body(doc, texte)

pb(doc)


# ════════════════════════════════════════════════════════════════════════════
# 14. ANNEXES TECHNIQUES
# ════════════════════════════════════════════════════════════════════════════
h1(doc, '14.  ANNEXES TECHNIQUES', sb=0)
add_hr(doc)

h2(doc, 'Annexe A – Endpoints API principaux')
body(doc,
    'La plateforme expose une API RESTful documentée via Swagger/ReDoc accessible à '
    '/api/v1/docs/ (authentification requise). Les principaux groupes d\'endpoints sont :')
api_groups = [
    ('/api/v1/auth/',              'Authentification : login, refresh token, logout, 2FA setup'),
    ('/api/v1/users/',             'Gestion des utilisateurs, profils, rôles, permissions'),
    ('/api/v1/enterprises/',       'Registre des entreprises, score conformité, documents'),
    ('/api/v1/complaints/',        'Plaintes : CRUD, assignation, changement de statut, pièces jointes'),
    ('/api/v1/inspections/',       'Zones, missions, rapports d\'inspection, PV'),
    ('/api/v1/mediations/',        'Séances de médiation, convocations, PV de conciliation'),
    ('/api/v1/judicial/',          'Procédures judiciaires, audiences, décisions'),
    ('/api/v1/domestic/',          'Travailleurs domestiques, contrats, certifications'),
    ('/api/v1/ai/',                'Chatbot juridique, analyse documentaire, transcription'),
    ('/api/v1/observatory/',       'Statistiques, rapports, indicateurs, exports'),
    ('/api/v1/bi/',                'Tableaux de bord, widgets, rapports personnalisés'),
    ('/api/v1/ged/',               'Documents, versionnage, audit trail GED'),
    ('/api/v1/notifications/',     'Préférences, historique des notifications'),
    ('/api/v1/administration/',    'Configuration système, audit log, paramètres'),
    ('/api/v1/landing/',           'Articles, FAQ, annuaires des directions'),
]
t_api = doc.add_table(rows=len(api_groups) + 1, cols=2)
t_api.style = 'Table Grid'
t_api.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl_header_row(t_api.rows[0], ['Endpoint', 'Fonctionnalités couvertes'])
for i, (ep, desc) in enumerate(api_groups, 1):
    bg = 'F5F7FA' if i % 2 == 0 else 'FFFFFF'
    tbl_data_cell(t_api.rows[i].cells[0], ep,   bg=bg, txt_color=VERT_CI, bold=True)
    tbl_data_cell(t_api.rows[i].cells[1], desc, bg=bg)

h2(doc, 'Annexe B – Schéma d\'intégration avec les systèmes existants')
body(doc, 'La plateforme prévoit les intégrations suivantes avec les systèmes tiers ivoiriens :')
integ = [
    ('CNPS (Caisse Nationale de Prévoyance Sociale)', 'Vérification en temps réel de l\'immatriculation et de la situation cotisante d\'une entreprise lors du dépôt d\'une plainte.'),
    ('DGI / e-impôts', 'Validation du NIF des entreprises enregistrées dans la plateforme.'),
    ('RCCM (Registre du Commerce)', 'Vérification et enrichissement des données des entreprises depuis le Greffe du Tribunal de Commerce.'),
    ('e-services.ci', 'Portail unique des services publics ivoiriens — interconnexion pour la connexion citoyenne (SSO).'),
    ('Orange CI / MTN CI / Moov Africa', 'Gateway SMS pour l\'envoi de notifications et d\'OTP aux utilisateurs mobiles.'),
    ('CinetPay / Bizao', 'Paiement en ligne des frais de dépôt de dossier (si applicable dans une phase ultérieure).'),
]
t_int = doc.add_table(rows=len(integ) + 1, cols=2)
t_int.style = 'Table Grid'
t_int.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl_header_row(t_int.rows[0], ['Système tiers', 'Nature de l\'intégration'])
for i, (sys, desc) in enumerate(integ, 1):
    bg = 'F5F7FA' if i % 2 == 0 else 'FFFFFF'
    tbl_data_cell(t_int.rows[i].cells[0], sys,  bg=bg, txt_color=BLEU_FONCE, bold=True)
    tbl_data_cell(t_int.rows[i].cells[1], desc, bg=bg)

h2(doc, 'Annexe C – Glossaire')
glossaire = [
    ('DGT', 'Direction Générale du Travail'),
    ('CNPS', 'Caisse Nationale de Prévoyance Sociale – Côte d\'Ivoire'),
    ('RCCM', 'Registre du Commerce et du Crédit Mobilier'),
    ('JWT', 'JSON Web Token – mécanisme d\'authentification sécurisé'),
    ('OTP', 'One-Time Password – code à usage unique pour l\'authentification 2FA'),
    ('GED', 'Gestion Électronique des Documents'),
    ('SLA', 'Service Level Agreement – accord sur les niveaux de service'),
    ('RBAC', 'Role-Based Access Control – contrôle d\'accès basé sur les rôles'),
    ('PV', 'Procès-Verbal (d\'infraction, de conciliation, de réception)'),
    ('OIT', 'Organisation Internationale du Travail (BIT en Français – Bureau International du Travail)'),
    ('OCR', 'Optical Character Recognition – reconnaissance optique de caractères'),
    ('CI/CD', 'Continuous Integration / Continuous Deployment – pratique DevOps de déploiement automatisé'),
    ('RTO', 'Recovery Time Objective – délai de reprise après incident'),
    ('RPO', 'Recovery Point Objective – perte de données maximale tolérée'),
    ('ARTCI', 'Autorité de Régulation des Télécommunications/TIC de Côte d\'Ivoire'),
]
t_glo = doc.add_table(rows=len(glossaire) + 1, cols=2)
t_glo.style = 'Table Grid'
t_glo.alignment = WD_TABLE_ALIGNMENT.CENTER
tbl_header_row(t_glo.rows[0], ['Sigle / Terme', 'Définition'])
for i, (terme, defn) in enumerate(glossaire, 1):
    bg = 'F5F7FA' if i % 2 == 0 else 'FFFFFF'
    tbl_data_cell(t_glo.rows[i].cells[0], terme, bg=bg, txt_color=BLEU_FONCE, bold=True)
    tbl_data_cell(t_glo.rows[i].cells[1], defn,  bg=bg)

doc.add_paragraph()
add_hr(doc, 'F47E1C', thick=8)


# ── Signature ────────────────────────────────────────────────────────────────
h1(doc, 'ACCEPTATION DE L\'OFFRE', size=14, sb=20)
body(doc,
    'Pour accepter la présente offre commerciale, veuillez retourner ce document signé, '
    'daté et revêtu du cachet officiel de la Direction Générale du Travail à l\'adresse : '
    'franckalain.ai@gmail.com — avec pour objet : « Acceptation Offre ' + REF + ' ».')

doc.add_paragraph()
t_sig = doc.add_table(rows=5, cols=2)
t_sig.style = 'Table Grid'
t_sig.alignment = WD_TABLE_ALIGNMENT.CENTER

sig_headers = ['Pour Numerix Digital', 'Pour la Direction Générale du Travail – CI']
for j, h in enumerate(sig_headers):
    c = t_sig.rows[0].cells[j]
    cell_bg(c, '00347C' if j == 0 else 'F47E1C')
    c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraphs[0].paragraph_format.space_before = Pt(8)
    c.paragraphs[0].paragraph_format.space_after  = Pt(8)
    r = c.paragraphs[0].add_run(h)
    r.bold = True; r.font.size = Pt(10); r.font.color.rgb = BLANC; r.font.name = 'Calibri'

for i, lbl in enumerate(['Nom et titre :', 'Date :', 'Signature :', 'Cachet officiel :'], 1):
    row = t_sig.rows[i]
    for j in range(2):
        c = row.cells[j]
        c.paragraphs[0].paragraph_format.space_before = Pt(5)
        c.paragraphs[0].paragraph_format.space_after  = Pt(18 if lbl in ('Signature :', 'Cachet officiel :') else 5)
        r = c.paragraphs[0].add_run(lbl)
        r.font.size = Pt(10); r.font.color.rgb = GRIS_TEXTE; r.font.name = 'Calibri'

doc.add_paragraph()

# Pied de page final
add_hr(doc, 'F47E1C', thick=4)
p_foot = doc.add_paragraph()
p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_foot.paragraph_format.space_before = Pt(8)
rf = p_foot.add_run(
    f'Numerix Digital  •  franckalain.ai@gmail.com  •  numerix.digital@gmail.com\n'
    f'Plateforme : api-e-inspection.numerix.digital  •  Réf. {REF}  •  {TODAY.strftime("%d %B %Y")}\n'
    f'Document confidentiel – Usage exclusif de la Direction Générale du Travail de Côte d\'Ivoire'
)
rf.font.size = Pt(8.5); rf.italic = True
rf.font.color.rgb = BLEU_MOYEN; rf.font.name = 'Calibri'

# ── Sauvegarde ────────────────────────────────────────────────────────────────
output = r'c:\Users\HP\Desktop\projets\plateforme-travail\backend\Offre_Commerciale_eInspection_DGT_CI_2026.docx'
doc.save(output)
print(f'Document généré : {output}')

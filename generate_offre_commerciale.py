"""
Génère l'offre commerciale de la plateforme e-Inspection du Travail CI
destinée à la Direction Générale du Travail (DGT) - Côte d'Ivoire
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

# ── Palette couleurs identité visuelle ──────────────────────────────────────
# Couleurs pour font.color.rgb (RGBColor)
ORANGE_CI    = RGBColor(0xE8, 0x6C, 0x00)
VERT_CI      = RGBColor(0x00, 0x7A, 0x3D)
BLANC        = RGBColor(0xFF, 0xFF, 0xFF)
GRIS_FONCE   = RGBColor(0x2D, 0x2D, 0x2D)
GRIS_MOYEN   = RGBColor(0x5A, 0x5A, 0x5A)
GRIS_CLAIR   = RGBColor(0xF2, 0xF2, 0xF2)
BLEU_ACIER   = RGBColor(0x1A, 0x3A, 0x5C)

# Couleurs pour les fonds de cellules (chaînes hex)
HEX_ORANGE   = 'E86C00'
HEX_VERT     = '007A3D'
HEX_BLANC    = 'FFFFFF'
HEX_GRIS_CL  = 'F2F2F2'
HEX_BLEU     = '1A3A5C'


# ── Helpers ──────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color: str):
    """hex_color : chaîne 6 caractères sans # ex: 'E86C00'"""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tc_pr.append(shd)


def set_cell_border(cell, **borders):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_borders = OxmlElement('w:tcBorders')
    for side, color in borders.items():
        border = OxmlElement(f'w:{side}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '6')
        border.set(qn('w:color'), color)
        tc_borders.append(border)
    tc_pr.append(tc_borders)


def heading(doc, text, level=1, color=BLEU_ACIER, size=16, bold=True, space_before=24, space_after=12):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after  = Pt(space_after)
    run = p.add_run(text)
    run.font.size   = Pt(size)
    run.font.bold   = bold
    run.font.color.rgb = color
    run.font.name   = 'Calibri'
    return p


def subheading(doc, text, color=ORANGE_CI, size=13):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(14)
    pf.space_after  = Pt(6)
    run = p.add_run(text)
    run.font.size  = Pt(size)
    run.font.bold  = True
    run.font.color.rgb = color
    run.font.name  = 'Calibri'
    return p


def body(doc, text, indent=0, color=GRIS_FONCE, size=11, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.left_indent  = Cm(indent)
    run = p.add_run(text)
    run.font.size   = Pt(size)
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name   = 'Calibri'
    return p


def bullet(doc, text, level=0, color=GRIS_FONCE):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent  = Cm(1.0 + level * 0.5)
    p.paragraph_format.space_after  = Pt(3)
    run = p.add_run(text)
    run.font.size  = Pt(10.5)
    run.font.color.rgb = color
    run.font.name  = 'Calibri'
    return p


def divider(doc, color='E86C00'):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    pPr  = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '12')
    bottom.set(qn('w:color'), color)
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def banner_row(doc, text, bg=HEX_BLEU, fg=BLANC, size=13):
    """Paragraphe pleine largeur façon bannière. bg = hex string 6 chars."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    cell = tbl.rows[0].cells[0]
    set_cell_bg(cell, bg)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    run = p.add_run(text)
    run.font.size  = Pt(size)
    run.font.bold  = True
    run.font.color.rgb = fg
    run.font.name  = 'Calibri'
    # Largeur maximale
    tbl.columns[0].width = Cm(17)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return tbl


def module_card(doc, numero, titre, sous_titre, fonctionnalites, roles, icone='▸'):
    """Carte détaillée d'un module."""
    subheading(doc, f'{icone}  Module {numero} — {titre}', color=BLEU_ACIER, size=13)
    if sous_titre:
        body(doc, sous_titre, indent=0.5, italic=True, color=GRIS_MOYEN)
    if fonctionnalites:
        body(doc, 'Fonctionnalités principales :', indent=0.5, color=GRIS_FONCE)
        for f in fonctionnalites:
            bullet(doc, f, level=1)
    if roles:
        body(doc, f'Profils concernés : {", ".join(roles)}', indent=0.5, color=VERT_CI, size=10)
    divider(doc, '007A3D')


def two_col_table(doc, rows_data, col1_header='', col2_header='', width_ratio=(6, 11)):
    """Tableau 2 colonnes avec entête colorée."""
    tbl = doc.add_table(rows=1 + len(rows_data), cols=2)
    tbl.style = 'Table Grid'
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    # En-têtes
    for i, hdr in enumerate([col1_header, col2_header]):
        cell = tbl.rows[0].cells[i]
        set_cell_bg(cell, HEX_BLEU)
        p = cell.paragraphs[0]
        run = p.add_run(hdr)
        run.font.bold = True
        run.font.color.rgb = BLANC
        run.font.size = Pt(10.5)
        run.font.name = 'Calibri'
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Données
    for r_idx, (c1, c2) in enumerate(rows_data):
        row = tbl.rows[r_idx + 1]
        bg_hex = HEX_GRIS_CL if r_idx % 2 == 0 else HEX_BLANC
        for c_idx, val in enumerate([c1, c2]):
            cell = row.cells[c_idx]
            set_cell_bg(cell, bg_hex)
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            run.font.size = Pt(10)
            run.font.name = 'Calibri'
    # Largeurs
    for row in tbl.rows:
        row.cells[0].width = Cm(width_ratio[0])
        row.cells[1].width = Cm(width_ratio[1])
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return tbl


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def generate():
    doc = Document()

    # ── Marges ────────────────────────────────────────────────────────────────
    for section in doc.sections:
        section.page_width   = Cm(21)
        section.page_height  = Cm(29.7)
        section.top_margin   = Cm(2.0)
        section.bottom_margin= Cm(2.0)
        section.left_margin  = Cm(2.5)
        section.right_margin = Cm(2.5)

    # ═══════════════════════════════════════════════════════════════════════
    # PAGE DE GARDE
    # ═══════════════════════════════════════════════════════════════════════

    # Bandeau supérieur orange
    tbl_top = doc.add_table(rows=1, cols=1)
    cell_top = tbl_top.rows[0].cells[0]
    set_cell_bg(cell_top, HEX_ORANGE)
    cell_top.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_top = cell_top.paragraphs[0].add_run('OFFRE COMMERCIALE CONFIDENTIELLE')
    run_top.font.bold  = True
    run_top.font.size  = Pt(10)
    run_top.font.color.rgb = BLANC
    run_top.font.name  = 'Calibri'
    tbl_top.columns[0].width = Cm(17)

    doc.add_paragraph()

    # Logo / Titre principal
    p_logo = doc.add_paragraph()
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_logo = p_logo.add_run('e-Inspection CI')
    run_logo.font.size  = Pt(42)
    run_logo.font.bold  = True
    run_logo.font.color.rgb = BLEU_ACIER
    run_logo.font.name  = 'Calibri'

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run('Plateforme Numérique de l\'Inspection du Travail')
    run_sub.font.size  = Pt(18)
    run_sub.font.bold  = False
    run_sub.font.color.rgb = ORANGE_CI
    run_sub.font.name  = 'Calibri'

    doc.add_paragraph()

    # Ligne séparatrice verte
    divider(doc, '007A3D')

    p_dest = doc.add_paragraph()
    p_dest.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_d = p_dest.add_run('Présentée à :\nDirection Générale du Travail (DGT)\nMinistère du Travail et de la Protection Sociale\nRépublique de Côte d\'Ivoire')
    run_d.font.size  = Pt(13)
    run_d.font.bold  = True
    run_d.font.color.rgb = BLEU_ACIER
    run_d.font.name  = 'Calibri'

    doc.add_paragraph()
    divider(doc, 'E86C00')
    doc.add_paragraph()

    # Informations offre
    info_data = [
        ('Référence offre',    'eIC-DGT-2026-001'),
        ('Date',               datetime.date.today().strftime('%d %B %Y')),
        ('Version',            '1.0 — Document confidentiel'),
        ('Durée de validité',  '90 jours à compter de la date d\'émission'),
        ('Interlocuteur',      'Direction e-Inspection CI'),
        ('Contact',            'contact@einspection.ci | +225 XX XX XX XX'),
    ]
    two_col_table(doc, info_data, 'Rubrique', 'Détail', (5, 12))

    doc.add_paragraph()

    # Bandeau vert bas de page de garde
    tbl_bot = doc.add_table(rows=1, cols=1)
    cell_bot = tbl_bot.rows[0].cells[0]
    set_cell_bg(cell_bot, HEX_VERT)
    cell_bot.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_bot = cell_bot.paragraphs[0].add_run(
        'Ce document contient des informations commerciales confidentielles.\n'
        'Sa diffusion est strictement réservée aux destinataires désignés.'
    )
    run_bot.font.size  = Pt(9)
    run_bot.font.color.rgb = BLANC
    run_bot.font.name  = 'Calibri'
    tbl_bot.columns[0].width = Cm(17)

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # SOMMAIRE
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, 'Sommaire', level=1, size=18, color=BLEU_ACIER, space_before=0)
    divider(doc)

    sommaire = [
        ('1.', 'Résumé Exécutif', '3'),
        ('2.', 'Contexte et Enjeux', '4'),
        ('3.', 'Présentation de la Plateforme e-Inspection CI', '5'),
        ('4.', 'Les 15 Modules Fonctionnels', '6'),
        ('   4.1', 'Gestion des Utilisateurs & Authentification', '6'),
        ('   4.2', 'Registre des Entreprises', '7'),
        ('   4.3', 'Gestion des Plaintes', '8'),
        ('   4.4', 'Inspections du Travail', '9'),
        ('   4.5', 'Conciliation & Médiation', '10'),
        ('   4.6', 'Procédures Judiciaires', '11'),
        ('   4.7', 'Emploi Domestique', '12'),
        ('   4.8', 'Hiérarchie & Workflow de Validation', '13'),
        ('   4.9', 'Intelligence Artificielle & Chatbot', '14'),
        ('   4.10', 'Observatoire du Travail', '15'),
        ('   4.11', 'Gestion Électronique de Documents (GED)', '15'),
        ('   4.12', 'Administration & Sécurité Système', '16'),
        ('   4.13', 'Business Intelligence & Tableaux de Bord', '16'),
        ('   4.14', 'Notifications Multi-Canaux', '17'),
        ('   4.15', 'Portail Public & Site Vitrine', '17'),
        ('5.', 'Application Mobile', '18'),
        ('6.', 'Architecture Technique', '19'),
        ('7.', 'Sécurité & Conformité', '20'),
        ('8.', 'Déploiement, Formation & Support', '21'),
        ('9.', 'Offre Tarifaire', '22'),
        ('10.', 'Planning de Mise en Œuvre', '23'),
        ('11.', 'Engagements Qualité & SLA', '24'),
    ]
    for num, titre, page in sommaire:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after  = Pt(2)
        tab_stops = p.paragraph_format.tab_stops
        run_n = p.add_run(f'{num}  {titre}')
        run_n.font.size  = Pt(10.5)
        run_n.font.name  = 'Calibri'
        if num.strip() in [str(i)+'.' for i in range(1, 12)]:
            run_n.font.bold = True
            run_n.font.color.rgb = BLEU_ACIER

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # 1. RÉSUMÉ EXÉCUTIF
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, '1. Résumé Exécutif', size=16, color=BLEU_ACIER)
    divider(doc)

    body(doc, (
        'e-Inspection CI est une plateforme numérique complète développée pour moderniser et dématérialiser '
        'l\'ensemble des activités de l\'Inspection du Travail en République de Côte d\'Ivoire. Conçue en '
        'conformité avec le Code du Travail ivoirien (Loi n° 2015-532 du 20 juillet 2015), elle couvre '
        'le cycle de vie complet du droit du travail : du dépôt de plainte jusqu\'à la décision judiciaire, '
        'en passant par la médiation, l\'inspection terrain et la gestion des travailleurs domestiques.'
    ))

    doc.add_paragraph()
    banner_row(doc, 'Une solution 360° pensée pour la DGT, les Inspecteurs et les Citoyens', HEX_BLEU)

    doc.add_paragraph()

    kpi_data = [
        ('15 modules fonctionnels',     'Couvrant l\'intégralité des métiers de l\'Inspection du Travail'),
        ('3 interfaces',                 'Web (React), Mobile (iOS/Android), API REST pour intégrations tierces'),
        ('8 profils d\'utilisateurs',    'Du citoyen à la Direction Générale, chaque rôle dispose d\'un espace dédié'),
        ('Architecture cloud-ready',     'Django 5 + MySQL + Redis + Celery — déployable en SaaS ou on-premise'),
        ('Sécurité renforcée',           'JWT + OTP/2FA + RBAC granulaire + protection OWASP Top 10'),
        ('IA intégrée',                  'Chatbot juridique Claude/OpenAI, détection d\'abus, prédiction de risques'),
        ('Notifications multi-canaux',   'Email, SMS, push mobile — avec retry automatique Celery'),
        ('100% conforme Code du Travail CI', 'SMIG, préavis, congés, procédures selon Loi 2015-532'),
    ]
    two_col_table(doc, kpi_data, 'Indicateur clé', 'Description', (5, 12))

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # 2. CONTEXTE ET ENJEUX
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, '2. Contexte et Enjeux', size=16, color=BLEU_ACIER)
    divider(doc)

    subheading(doc, '2.1 Un défi structurel pour la DGT')
    body(doc, (
        'La Direction Générale du Travail de Côte d\'Ivoire fait face à des défis majeurs dans l\'exercice '
        'de ses missions de contrôle, de médiation et de protection des travailleurs :'
    ))
    for enjeu in [
        'Gestion manuelle et fragmentée des plaintes laborales — délais de traitement excessifs',
        'Convocations de médiation ignorées par les employeurs — absence de mécanisme de suivi',
        'Inspections terrain sans outil numérique — rapports papier non exploitables en temps réel',
        'Travailleurs domestiques exclus du système formel — vulnérabilité extrême non détectée',
        'Absence de tableau de bord consolidé pour la prise de décision à la direction',
        'Données éparpillées entre bureaux régionaux — impossibilité de vision nationale',
        'Procédures judiciaires sans traçabilité numérique — risques de perte de dossiers',
    ]:
        bullet(doc, enjeu)

    subheading(doc, '2.2 Le contexte réglementaire')
    regl_data = [
        ('Code du Travail CI',     'Loi n° 2015-532 du 20 juillet 2015 — référence centrale de la plateforme'),
        ('SMIG',                   '75 000 FCFA/mois — intégré dans tous les calculs salariaux'),
        ('Durée légale du travail','8h/jour, 40h/semaine (Art. 21.1) — contrôle automatisé'),
        ('Congés payés',           '2,5 jours/mois travaillé (Art. 25.1) — calcul automatique'),
        ('Préavis de licenciement','1 à 3 mois selon ancienneté (Art. 18.1) — guide intégré'),
        ('Heure supplémentaire',   '+15% (1-8h) puis +50% (>8h) (Art. 21.2) — alertes automatiques'),
        ('CNPS',                   'Cotisations employé 6,3% — calcul intégré dans bulletins domestiques'),
    ]
    two_col_table(doc, regl_data, 'Réglementation', 'Application dans la plateforme', (5, 12))

    subheading(doc, '2.3 La réponse e-Inspection CI')
    body(doc, (
        'e-Inspection CI répond à ces défis par une architecture modulaire et intégrée qui place le citoyen, '
        'le travailleur et l\'inspecteur au centre d\'un écosystème numérique cohérent, conforme et sécurisé. '
        'Chaque module a été conçu en collaboration avec les métiers de l\'inspection du travail pour '
        'garantir l\'adéquation fonctionnelle avec les réalités ivoiriennes.'
    ))

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # 3. PRÉSENTATION DE LA PLATEFORME
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, '3. Présentation de la Plateforme e-Inspection CI', size=16, color=BLEU_ACIER)
    divider(doc)

    subheading(doc, '3.1 Vision et ambition')
    body(doc, (
        'e-Inspection CI se positionne comme le système d\'information de référence de l\'Inspection du Travail '
        'ivoirienne. La plateforme unifie en un seul écosystème numérique tous les acteurs du monde du travail : '
        'les travailleurs qui déposent des plaintes, les inspecteurs qui les traitent, les employeurs qui répondent '
        'aux convocations, et la direction qui pilote et supervise l\'ensemble.'
    ))

    subheading(doc, '3.2 Profils utilisateurs et espaces dédiés')
    profils_data = [
        ('EMPLOYE / EMPLOYE_MAISON', 'Dépôt de plainte, suivi en temps réel, espace personnel, pointage GPS, bulletins de paie'),
        ('EMPLOYEUR',                'Réponse aux convocations, gestion des travailleurs domestiques, contrats, congés'),
        ('INSPECTEUR',               'Tableau de bord terrain, dossiers, inspections, médiations, carnet d\'adresses, cartographie'),
        ('CHEF_INSPECTION',          'Supervision équipe, assignation de dossiers, validation, escalades, délégations'),
        ('DIRECTEUR_REGIONAL',       'Vue régionale consolidée, approbations, statistiques régionales, alertes'),
        ('DIRECTEUR_GENERAL',        'Dashboard exécutif national, KPIs stratégiques, tendances, observatoire'),
        ('ADMIN',                    'Configuration système, gestion utilisateurs, audit logs, matrice des permissions'),
        ('PUBLIC (non connecté)',     'Portail public : actualités, FAQ, assistant IA, localisation bureaux d\'inspection'),
    ]
    two_col_table(doc, profils_data, 'Profil', 'Accès et fonctionnalités', (4, 13))

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # 4. LES 15 MODULES FONCTIONNELS
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, '4. Les 15 Modules Fonctionnels', size=16, color=BLEU_ACIER)
    divider(doc)

    body(doc, (
        'La plateforme est organisée en 15 modules fonctionnels indépendants mais interconnectés. '
        'Chaque module dispose de son propre ensemble d\'APIs REST, de ses interfaces utilisateur '
        'et de ses règles métier spécifiques au contexte ivoirien.'
    ))
    doc.add_paragraph()

    # ── Module 1 : Utilisateurs ────────────────────────────────────────────
    module_card(
        doc, '1', 'Gestion des Utilisateurs & Authentification',
        'Système d\'identité centralisé avec authentification forte (JWT + OTP/2FA), gestion des profils '
        'et sécurisation de tous les accès à la plateforme.',
        [
            'Inscription et connexion sécurisée par email et mot de passe (hachage bcrypt)',
            'Double authentification OTP (Google Authenticator, application mobile)',
            'Tokens JWT avec rotation automatique (access 30min + refresh 7j)',
            'Gestion de profil complet : photo, coordonnées, zone d\'affectation',
            'Récupération de mot de passe par email avec lien sécurisé à durée limitée',
            'Numéro de téléphone avec validation format +225 (Côte d\'Ivoire)',
            'Historique de connexion et journalisation des activités',
            'Blocage automatique après 5 tentatives échouées (protection brute-force)',
        ],
        ['Tous les profils (inscription publique puis affectation d\'un rôle par l\'Admin)']
    )

    # ── Module 2 : Entreprises ─────────────────────────────────────────────
    module_card(
        doc, '2', 'Registre National des Entreprises',
        'Annuaire complet des entreprises ivoiriennes avec scoring de conformité automatique, '
        'suivi des inspections et gestion documentaire.',
        [
            'Fiche entreprise complète : RCCM, NIF, secteur, effectif, adresse GPS',
            'Score de conformité (0-100) calculé automatiquement selon l\'historique des inspections',
            'Niveau de risque : FAIBLE, MOYEN, ÉLEVÉ, CRITIQUE — mis à jour en temps réel',
            'Gestion des établissements secondaires (multi-sites)',
            'Upload et suivi des documents obligatoires (CNPS, permis, certifications)',
            'Historique complet des événements : inspections, plaintes, médiations',
            'Filtre et recherche avancée par secteur, zone, risque, conformité',
            'Export CSV/Excel de la liste des entreprises',
        ],
        ['Inspecteur', 'Chef Inspection', 'Directeur', 'Admin']
    )

    # ── Module 3 : Plaintes ────────────────────────────────────────────────
    module_card(
        doc, '3', 'Gestion des Plaintes Laborales',
        'Circuit complet de traitement des plaintes de bout en bout — du dépôt citoyen jusqu\'à la résolution '
        'ou l\'escalade judiciaire, avec traçabilité totale et notifications automatiques.',
        [
            'Dépôt de plainte en ligne (web + mobile) avec pièces jointes',
            'Numérotation automatique (ex: PLT-CI-2026-00421)',
            'Types de plaintes : salaire impayé, licenciement abusif, harcèlement, heures sup, sécurité…',
            '4 niveaux de priorité : URGENT (48h), ÉLEVÉE (7j), MOYENNE (15j), NORMALE (30j)',
            'Assignation par le Chef Inspection à un inspecteur disponible',
            'Suivi du statut en temps réel par le plaignant (12 statuts distincts)',
            'Commentaires internes (visibles inspecteurs uniquement) et externes (plaignant)',
            'Escalade automatique Celery si délai dépassé — notification à la hiérarchie',
            'Rappels automatiques toutes les 72h pour les dossiers sans activité',
            'Historique complet des changements de statut avec horodatage et auteur',
            'Notifications automatiques à chaque changement (email + push mobile)',
        ],
        ['Employé', 'Employé de Maison', 'Inspecteur', 'Chef Inspection', 'Direction']
    )

    # ── Module 4 : Inspections ─────────────────────────────────────────────
    module_card(
        doc, '4', 'Inspections du Travail sur le Terrain',
        'Outil de planification et d\'exécution des inspections terrain avec géolocalisation, '
        'capture photos, optimisation d\'itinéraire et suivi GPS des inspecteurs.',
        [
            'Planification des inspections (routine, suivi, suite plainte, contrôle inopiné)',
            'Géolocalisation GPS de l\'inspecteur avec validation de présence sur site (géofencing 500m)',
            'Optimisation d\'itinéraire journalier pour minimiser les déplacements',
            'Capture et upload photos de preuves directement depuis l\'application mobile',
            'Rapport d\'inspection numérique : constats, infractions, recommandations',
            '4 résultats d\'inspection : CONFORME, PROBLÈMES MINEURS, MAJEURS, NON CONFORME',
            'Mise à jour automatique du score de conformité de l\'entreprise après inspection',
            'Carte de chaleur (heatmap) des zones à risque',
            'Zones de risque géographiques avec alertes pour l\'inspecteur terrain',
            'Planning hebdomadaire / mensuel avec vue calendrier',
            'Statistiques personnelles de chaque inspecteur',
        ],
        ['Inspecteur', 'Chef Inspection', 'Directeur']
    )

    # ── Module 5 : Médiation ───────────────────────────────────────────────
    module_card(
        doc, '5', 'Conciliation & Médiation',
        'Module phare répondant au problème central des employeurs qui refusent les convocations. '
        'Système de triple convocation avec escalade automatique et constat officiel de non-comparution.',
        [
            'Création de séances de médiation liées à une plainte',
            'Convocation officielle tri-canal : email + SMS + notification in-app',
            'Suivi individuel de chaque partie : accusé de réception, présence confirmée',
            '3 tentatives maximum de convocation (72h entre chaque tentative)',
            'Constat officiel de non-comparution après 3 tentatives infructueuses (Art. 79.3 Code du Travail)',
            'Escalade automatique à la hiérarchie avec rapport d\'absence',
            'Possibilité de relancer une convocation manuellement depuis l\'app mobile inspecteur',
            'Procès-verbal de séance numérique avec signatures électroniques',
            'Accord de médiation formalisé avec suivi de mise en œuvre',
            'Statuts multiples : CONVOQUÉ, CONFIRMÉ, TENU, REPORTÉ, EMPLOYEUR_ABSENT, ESCALADÉ',
            'Dashboard temps réel : médiations en cours, taux de succès, taux de non-comparution',
            'Application mobile : bouton "Constater la non-comparution" pour l\'inspecteur terrain',
        ],
        ['Inspecteur', 'Chef Inspection', 'Employé', 'Employeur']
    )

    # ── Module 6 : Judiciaire ──────────────────────────────────────────────
    module_card(
        doc, '6', 'Procédures Judiciaires',
        'Suivi complet des dossiers transmis aux juridictions du travail, '
        'de la saisine jusqu\'à la décision finale.',
        [
            'Ouverture d\'une procédure judiciaire depuis une plainte non résolue',
            'Transmission dématérialisée du dossier au tribunal compétent',
            'Suivi des audiences : programmation, rappels -48h/-24h automatiques (Celery)',
            'Enregistrement des présences à l\'audience (plaignant, défendeur)',
            'Upload des pièces de procédure (assignations, mémoires, décisions)',
            'Enregistrement de la décision judiciaire : type, dispositif, délais d\'appel',
            'Alertes automatiques pour les procédures sans activité depuis 30 jours',
            'Mise à jour automatique du statut de la plainte à chaque étape',
            'Tableau de bord des affaires en instance par juridiction',
        ],
        ['Inspecteur', 'Chef Inspection', 'Directeur']
    )

    # ── Module 7 : Emploi Domestique ───────────────────────────────────────
    module_card(
        doc, '7', 'Emploi Domestique & Travailleurs Vulnérables',
        'Module spécialisé pour la formalisation et le suivi des travailleurs domestiques '
        'en Côte d\'Ivoire, population historiquement exclue de la protection du travail formel.',
        [
            'Enregistrement des travailleurs domestiques (gardiens, cuisiniers, aides-ménagères, nounous)',
            'Signature numérique du contrat de travail (CDD/CDI) par les deux parties',
            'Suivi des contrats actifs avec alertes d\'expiration et renouvellement automatique',
            'Calcul automatique du SMIG et vérification de conformité salariale',
            'Bulletins de paie mensuels générés automatiquement le 1er de chaque mois (Celery)',
            'Calcul net/brut avec déduction CNPS employé (6,3%) conforme à la réglementation CI',
            'Pointage GPS : check-in/check-out avec validation géofencing 500m du lieu de travail',
            'Gestion des demandes de congé avec validation employeur (rappels 48h si pas de réponse)',
            'Heures supplémentaires : saisie, validation, calcul majorations automatiques',
            'Réclamation vocale : l\'employé de maison peut déposer une réclamation par message vocal',
            'Visites terrain de l\'inspecteur avec enregistrement GPS et photos',
            'Expiration automatique des contrats échus (tâche Celery nocturne)',
        ],
        ['Employé de Maison', 'Employeur (particulier)', 'Inspecteur']
    )

    # ── Module 8 : Hiérarchie ──────────────────────────────────────────────
    module_card(
        doc, '8', 'Hiérarchie & Workflow de Validation',
        'Gestion des circuits d\'approbation à plusieurs niveaux, des escalades, '
        'des délégations et des réaffectations de dossiers.',
        [
            'Workflow d\'approbation à 3 niveaux : Chef Inspection → Directeur Régional → DG',
            'Escalade manuelle ou automatique des dossiers sensibles',
            'Système de délégation temporaire de pouvoirs (congés, absences)',
            'Réaffectation de dossiers entre inspecteurs avec traçabilité complète',
            'Notifications à chaque étape d\'approbation ou de rejet',
            'Tableau de bord des dossiers en attente d\'approbation par approbateur',
            'Historique détaillé des réaffectations avec motif et signataire',
            'Alerte automatique si un dossier attend une approbation depuis plus de 48h',
        ],
        ['Chef Inspection', 'Directeur Régional', 'Directeur Général', 'Admin']
    )

    # ── Module 9 : IA ──────────────────────────────────────────────────────
    module_card(
        doc, '9', 'Intelligence Artificielle & Chatbot Juridique',
        'Assistant juridique intelligent basé sur Claude (Anthropic) ou GPT-4o '
        'avec connaissance du Code du Travail ivoirien, analyse de contrats OCR '
        'et détection précoce des abus.',
        [
            'Chatbot juridique 24h/24 répondant aux questions sur le droit du travail CI',
            'Base de connaissances : Code du Travail Loi 2015-532, SMIG, préavis, congés, CNPS',
            'Intégration Claude API (Anthropic claude-haiku) ou OpenAI GPT-4o-mini',
            'Fallback simulation si aucune clé API configurée (aucune interruption de service)',
            'Historique des conversations par utilisateur avec contexte maintenu',
            'Analyse OCR des contrats de travail uploadés : détection de clauses abusives',
            'Détection automatique des abus : harcèlement, travail forcé, travail des enfants',
            'Prédiction de risques sociaux par entreprise (grève, litige, non-conformité)',
            'Recherche de plaintes similaires pour détecter les employeurs récidivistes',
            'Assistant pré-remplissage de formulaire de plainte depuis la conversation',
        ],
        ['Tous les profils — accès universel']
    )

    # ── Module 10 : Observatoire ───────────────────────────────────────────
    module_card(
        doc, '10', 'Observatoire du Travail',
        'Centre de données temps réel pour le pilotage national de l\'Inspection du Travail '
        'avec vues consolidées par région, secteur et type de violation.',
        [
            'Statistiques nationales temps réel : plaintes, inspections, médiations, entreprises',
            'Tendances sur 7/30/90 jours avec graphiques d\'évolution',
            'Répartition des plaintes par type, région et secteur d\'activité',
            'Top entreprises les plus plaignées — tableau de bord de surveillance',
            'Métriques de performance : délai moyen de résolution, taux de médiation réussie',
            'Conformité moyenne par secteur d\'activité',
            'Dashboard exécutif réservé au Directeur Général et à la Direction',
            'Alertes KPI : seuils critiques déclenchant des notifications automatiques',
        ],
        ['Inspecteur (lecture)', 'Chef Inspection', 'Direction', 'Directeur Général']
    )

    # ── Module 11 : GED ────────────────────────────────────────────────────
    module_card(
        doc, '11', 'Gestion Électronique de Documents (GED)',
        'Système centralisé de gestion documentaire pour archiver, organiser et retrouver '
        'rapidement tous les documents produits par l\'Inspection du Travail.',
        [
            'Organisation par catégories et sous-catégories (contrats, PV, décisions, circulaires…)',
            'Versioning : conservation de toutes les versions d\'un document',
            'Recherche fulltext dans les titres et descriptions des documents',
            'Journalisation des accès : qui a consulté ou téléchargé quel document, quand',
            'Archivage électronique avec horodatage légal',
            'Partage sécurisé entre services et bureaux régionaux',
            'Restauration de documents archivés si nécessaire',
        ],
        ['Inspecteur', 'Chef Inspection', 'Direction']
    )

    # ── Module 12 : Administration ─────────────────────────────────────────
    module_card(
        doc, '12', 'Administration & Sécurité Système',
        'Back-office complet pour l\'administration technique et la gouvernance de la plateforme.',
        [
            'Gestion des comptes utilisateurs : création, activation, suspension, suppression',
            'Matrice des permissions RBAC configurable : 8 rôles × N actions',
            'Journal d\'audit complet : toutes les actions enregistrées (qui, quoi, quand, d\'où)',
            'Configuration système : paramètres globaux, URLs, clés API, seuils d\'alerte',
            'Gestion des modes maintenance avec message personnalisé',
            'Journalisation des sauvegardes avec statut et historique',
            'Statistiques d\'utilisation de la plateforme par module',
            'Gestion des rôles et permissions par interface graphique',
        ],
        ['Admin uniquement']
    )

    # ── Module 13 : BI ─────────────────────────────────────────────────────
    module_card(
        doc, '13', 'Business Intelligence & Tableaux de Bord',
        'Outils d\'analyse décisionnelle avec rapports personnalisés, KPIs stratégiques '
        'et exports automatisés.',
        [
            'Création de rapports personnalisés avec requêtes SELECT sécurisées (Admin uniquement)',
            'Protection anti-injection SQL : validation regex obligatoire SELECT-only',
            'KPIs configurables : valeur cible, seuil d\'alerte, seuil critique',
            'Tableaux de bord personnalisables par profil utilisateur',
            'Exports automatisés (CSV, Excel, JSON) via tâches Celery asynchrones',
            'Historique des exports avec statut (en cours, terminé, échoué)',
            'Accès restreint : Chef Inspection et niveaux supérieurs uniquement',
        ],
        ['Chef Inspection', 'Directeur Régional', 'Directeur Général', 'Admin']
    )

    # ── Module 14 : Notifications ──────────────────────────────────────────
    module_card(
        doc, '14', 'Notifications Multi-Canaux',
        'Infrastructure de communication automatisée assurant qu\'aucune action critique '
        'ne passe inaperçue, avec retry automatique en cas d\'échec.',
        [
            'Notifications in-app en temps réel (WebSocket Django Channels)',
            'Envoi d\'emails avec gestion de templates HTML personnalisables (10 types)',
            'SMS sortants avec fournisseur configurable (Africa\'s Talking, Twilio)',
            'Push notifications mobile (iOS et Android)',
            'Retry automatique des envois échoués toutes les 30 minutes (Celery)',
            'Traitement de la file d\'attente toutes les 5 minutes',
            'Journalisation complète : statut, date d\'envoi, erreurs, nombre de tentatives',
            'Templates d\'email éditables par l\'administrateur',
        ],
        ['Tous les profils — envoi automatique selon les événements']
    )

    # ── Module 15 : Landing ────────────────────────────────────────────────
    module_card(
        doc, '15', 'Portail Public & Site Vitrine',
        'Face publique de la plateforme accessible sans connexion — vitrine institutionnelle '
        'du Ministère du Travail avec services aux citoyens.',
        [
            'Page d\'accueil avec statistiques nationales temps réel (plaintes, inspections, médiations)',
            'Actualités et communiqués du MINTSS',
            'FAQ droit du travail CI avec recherche',
            'Assistant IA public : réponses automatiques aux questions juridiques courantes',
            'Localisation des bureaux d\'inspection par carte interactive',
            'Téléchargement de formulaires officiels (déclarations, modèles de contrats)',
            'Textes réglementaires (Code du Travail, décrets d\'application)',
            'Témoignages et campagnes de sensibilisation',
            'Formulaire de contact pour demandes d\'information',
            'Interface d\'administration dédiée pour la mise à jour des contenus (Admin)',
        ],
        ['Public (accès sans compte)', 'Admin (gestion du contenu)']
    )

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # 5. APPLICATION MOBILE
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, '5. Application Mobile', size=16, color=BLEU_ACIER)
    divider(doc)

    body(doc, (
        'La plateforme e-Inspection CI comprend une application mobile native développée avec React Native / Expo, '
        'disponible sur iOS et Android. Elle offre les fonctionnalités essentielles optimisées pour l\'usage terrain.'
    ))

    mobile_data = [
        ('Espace Inspecteur',        'Tableau de bord, dossiers assignés, planning GPS, convocations, PV numériques'),
        ('Espace Employé',           'Mes plaintes, suivi statut, pointage GPS, congés, bulletins de paie'),
        ('Espace Employeur',         'Mes travailleurs, contrats, validation congés, réponse aux convocations'),
        ('Médiations Mobile',        'Relance de convocation, constat de non-comparution, PV de séance'),
        ('Notifications Push',       'Alertes temps réel même en arrière-plan'),
        ('Mode hors-connexion',      'Consultation des données préchargées sans réseau (synchronisation à reconnexion)'),
        ('Géolocalisation',          'Validation présence sur site, itinéraire optimisé, zones de risque'),
        ('Sécurité mobile',          'Authentification biométrique (empreinte, Face ID) + JWT renouvelé automatiquement'),
    ]
    two_col_table(doc, mobile_data, 'Fonctionnalité', 'Description', (5, 12))

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # 6. ARCHITECTURE TECHNIQUE
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, '6. Architecture Technique', size=16, color=BLEU_ACIER)
    divider(doc)

    subheading(doc, '6.1 Stack Technologique')
    tech_data = [
        ('Backend API',      'Django 5.0.6 + Django REST Framework 3.15.1 (Python 3.12)'),
        ('Base de données',  'MySQL / MariaDB — transactions ACID, isolation READ COMMITTED'),
        ('Cache & Broker',   'Redis 7+ — sessions, cache, broker Celery, WebSocket pub-sub'),
        ('Tâches asynchrones','Celery 5.3.6 + Celery Beat — 12 tâches planifiées (crontab)'),
        ('WebSockets',       'Django Channels 4.1.0 — notifications temps réel'),
        ('Frontend Web',     'React 18 + TypeScript + Vite — SPA responsive'),
        ('Application Mobile','React Native / Expo SDK 50+ — iOS & Android natif'),
        ('Documentation API','drf-spectacular (OpenAPI 3.0 / Swagger UI)'),
        ('Génération docs',  'python-docx — export Word automatisé'),
        ('IA / LLM',         'Claude API (Anthropic) + OpenAI GPT-4o-mini en fallback'),
        ('OCR',              'Tesseract + Pillow — analyse documents uploadés'),
        ('Authentification', 'SimpleJWT (access 30min / refresh 7j) + pyotp (2FA)'),
    ]
    two_col_table(doc, tech_data, 'Composant', 'Technologie', (5, 12))

    subheading(doc, '6.2 Architecture des microservices applicatifs')
    body(doc, 'La plateforme suit une architecture modulaire Django avec 15 applications distinctes :')
    for app in [
        'users — Authentification et profils utilisateurs',
        'enterprises — Registre des entreprises',
        'complaints — Circuit de plaintes laborales',
        'inspections — Inspections terrain et zones',
        'mediations — Conciliation et médiation',
        'judicial — Procédures judiciaires',
        'domestic — Emploi domestique',
        'hierarchy — Workflows et approbations',
        'ai — Chatbot, OCR, similarité, détection abus',
        'observatory — Statistiques et observatoire national',
        'ged — Gestion documentaire électronique',
        'administration — Back-office et audit',
        'bi — Business Intelligence et exports',
        'notifications — Email, SMS, push multi-canal',
        'landing — Portail public et site vitrine',
    ]:
        bullet(doc, app, level=0)

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # 7. SÉCURITÉ & CONFORMITÉ
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, '7. Sécurité & Conformité', size=16, color=BLEU_ACIER)
    divider(doc)

    secu_data = [
        ('Authentification forte',      'JWT (access 30min) + Refresh token 7j + OTP/TOTP 2FA optionnel'),
        ('Contrôle d\'accès (RBAC)',     '8 rôles × N permissions — matrice granulaire — vérifiée à chaque requête'),
        ('Protection OWASP Top 10',     'Validation entrées, protection XSS, CSRF, injection SQL (regex SELECT-only)'),
        ('Chiffrement des données',     'HTTPS/TLS obligatoire — mots de passe hachés bcrypt'),
        ('Journal d\'audit complet',    'Chaque action enregistrée : user, IP, horodatage, action, ressource cible'),
        ('Protection brute-force',      'Blocage après 5 tentatives — délai exponentiel'),
        ('Isolation des données',       'Chaque utilisateur voit uniquement les données de son périmètre'),
        ('Sauvegardes',                 'Sauvegardes planifiées avec journalisation des backups et restauration testée'),
        ('Données personnelles',        'Conformité RGPD-compatible — droit à l\'effacement et à la portabilité'),
    ]
    two_col_table(doc, secu_data, 'Mesure de sécurité', 'Implémentation', (5, 12))

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # 8. DÉPLOIEMENT, FORMATION & SUPPORT
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, '8. Déploiement, Formation & Support', size=16, color=BLEU_ACIER)
    divider(doc)

    subheading(doc, '8.1 Options de déploiement')
    deploy_data = [
        ('SaaS Cloud',        'Hébergement géré sur infrastructure cloud (OVH, AWS ou serveurs africains) — maintenances incluses'),
        ('On-Premise DGT',    'Déploiement sur les serveurs du MINTSS — transfert de compétences assuré'),
        ('Hybride',           'API en cloud, données sensibles on-premise — compromis sécurité/agilité'),
    ]
    two_col_table(doc, deploy_data, 'Mode', 'Description', (4, 13))

    subheading(doc, '8.2 Plan de formation')
    for f in [
        '5 jours — Formation administrateurs système (configuration, gestion utilisateurs, audit)',
        '3 jours — Formation Chefs d\'Inspection (workflow, escalades, tableaux de bord)',
        '2 jours — Formation Inspecteurs du Travail (espace inspecteur, mobile, terrain)',
        '1 jour  — Formation Directeurs (dashboard exécutif, observatoire, KPIs)',
        'Supports pédagogiques : guides utilisateur PDF, vidéos tutoriels, FAQ en ligne',
        'Hotline dédiée DGT pendant 3 mois post-déploiement',
    ]:
        bullet(doc, f)

    subheading(doc, '8.3 Niveaux de support')
    support_data = [
        ('Niveau 1', 'Support utilisateur',    '24h ouvrées', 'Tickets, email, téléphone'),
        ('Niveau 2', 'Support fonctionnel',    '4h ouvrées',  'Incidents métier, paramétrage'),
        ('Niveau 3', 'Support technique',      '2h',          'Bugs critiques, indisponibilité'),
        ('Niveau 4', 'Incident majeur',        '30 minutes',  'Perte de données, brèche sécurité'),
    ]
    tbl_sup = doc.add_table(rows=1 + len(support_data), cols=4)
    tbl_sup.style = 'Table Grid'
    for i, h in enumerate(['Niveau', 'Type', 'Délai réponse', 'Canaux']):
        cell = tbl_sup.rows[0].cells[i]
        set_cell_bg(cell, HEX_BLEU)
        run = cell.paragraphs[0].add_run(h)
        run.font.bold = True
        run.font.color.rgb = BLANC
        run.font.size = Pt(10.5)
        run.font.name = 'Calibri'
    for r_idx, row_data in enumerate(support_data):
        row = tbl_sup.rows[r_idx + 1]
        bg_hex2 = HEX_GRIS_CL if r_idx % 2 == 0 else HEX_BLANC
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            set_cell_bg(cell, bg_hex2)
            run = cell.paragraphs[0].add_run(str(val))
            run.font.size = Pt(10)
            run.font.name = 'Calibri'

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # 9. OFFRE TARIFAIRE
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, '9. Offre Tarifaire', size=16, color=BLEU_ACIER)
    divider(doc)

    banner_row(doc, 'Offre sur mesure — Tarification soumise à négociation avec la DGT', HEX_ORANGE)

    subheading(doc, '9.1 Composantes de l\'offre')
    tarif_data = [
        ('Licence plateforme (annuelle)',       'Accès illimité aux 15 modules + mises à jour majeures'),
        ('Déploiement & paramétrage',           'Installation, configuration, migration données existantes'),
        ('Application mobile (iOS + Android)',  'Publication sur App Store et Google Play + mises à jour'),
        ('Formation initiale',                  '5 jours sur site — tous profils — supports inclus'),
        ('Support & maintenance (annuelle)',    'Niveaux 1-4 — SLA contractualisé — correctifs illimités'),
        ('Hébergement sécurisé (optionnel)',    'Infrastructure cloud dédiée avec monitoring 24/7'),
        ('Développements spécifiques',          'Sur devis — évolutions métier propres à la DGT'),
    ]
    two_col_table(doc, tarif_data, 'Composante', 'Contenu', (6, 11))

    subheading(doc, '9.2 Options modulaires')
    body(doc, (
        'La DGT peut choisir de déployer la plateforme en totalité ou par lots fonctionnels prioritaires. '
        'Nous recommandons la priorisation suivante pour un démarrage rapide et un impact visible :'
    ))
    lots_data = [
        ('LOT 1 — Prioritaire (mois 1-3)',   'Plaintes + Médiations + Inspections + Mobile Inspecteur'),
        ('LOT 2 — Consolidation (mois 4-6)', 'Entreprises + Judiciaire + Hiérarchie + Notifications'),
        ('LOT 3 — Intelligence (mois 7-9)',  'IA + Observatoire + BI + GED + Dashboard DG'),
        ('LOT 4 — Inclusion (mois 10-12)',   'Emploi domestique + Portail public + Formation étendue'),
    ]
    two_col_table(doc, lots_data, 'Lot', 'Modules inclus', (6, 11))

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # 10. PLANNING DE MISE EN ŒUVRE
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, '10. Planning de Mise en Œuvre', size=16, color=BLEU_ACIER)
    divider(doc)

    plan_data = [
        ('Semaine 1-2',     'Cadrage & contractualisation',   'Validation périmètre, signature contrat, désignation équipe projet'),
        ('Semaine 3-4',     'Infrastructure',                 'Déploiement serveurs, domaine, SSL, base de données, configuration'),
        ('Semaine 5-8',     'LOT 1 — Déploiement',           'Plaintes, médiations, inspections, mobile inspecteur — tests UAT'),
        ('Semaine 9',       'Formation LOT 1',                'Formation inspecteurs et chefs d\'inspection sur site'),
        ('Semaine 10-12',   'Pilote régional',                'Déploiement pilote sur 1-2 directions régionales — retours terrain'),
        ('Mois 4-6',        'LOT 2-3 — Déploiement',         'Entreprises, judiciaire, BI, IA, observatoire — tests et ajustements'),
        ('Mois 6',          'Formation LOT 2-3',              'Formation direction, chefs inspection, administrateurs'),
        ('Mois 7-9',        'LOT 4 — Déploiement',           'Emploi domestique, portail public, formation étendue'),
        ('Mois 10',         'Déploiement national',           'Ouverture à l\'ensemble des bureaux d\'inspection CI'),
        ('Mois 11-12',      'Stabilisation & accompagnement','Monitoring intensif, corrections, optimisations, bilan annuel'),
    ]
    two_col_table(doc, [(a, b + ' — ' + c) for a, b, c in plan_data], 'Période', 'Activité et livrables', (3, 14))

    doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════
    # 11. ENGAGEMENTS QUALITÉ & SLA
    # ═══════════════════════════════════════════════════════════════════════

    heading(doc, '11. Engagements Qualité & SLA', size=16, color=BLEU_ACIER)
    divider(doc)

    sla_data = [
        ('Disponibilité plateforme',    '99,5% uptime mensuel garanti (hors maintenance planifiée)'),
        ('Temps de réponse API',        '< 500ms pour 95% des requêtes en charge normale'),
        ('Sauvegarde quotidienne',      'Backup automatique chaque nuit + rétention 90 jours'),
        ('Restauration données',        'RTO < 4h, RPO < 24h en cas d\'incident majeur'),
        ('Correctifs de sécurité',      'Patch critique déployé sous 24h — patch majeur sous 72h'),
        ('Mises à jour fonctionnelles', '4 releases majeures/an + correctifs mineurs continus'),
        ('Tests de non-régression',     'Suite de tests automatisés à chaque déploiement'),
        ('Rapport mensuel',             'Rapport de performance, incidents, utilisation transmis à la DGT'),
    ]
    two_col_table(doc, sla_data, 'Engagement', 'Niveau garanti', (6, 11))

    doc.add_paragraph()
    banner_row(doc,
        'e-Inspection CI — La solution numérique de référence pour moderniser\n'
        'l\'Inspection du Travail en Côte d\'Ivoire',
        HEX_VERT
    )

    body(doc, (
        '\nNous remercions la Direction Générale du Travail de l\'attention portée à cette offre. '
        'Notre équipe est disponible pour une démonstration complète de la plateforme, '
        'une adaptation de l\'offre à vos besoins spécifiques, ou toute question complémentaire. '
        'Cette offre est valable 90 jours à compter de sa date d\'émission.'
    ), color=GRIS_MOYEN, size=10, italic=True)

    divider(doc, '1A3A5C')

    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run_sign = p_sign.add_run(
        f'Fait à Abidjan, le {datetime.date.today().strftime("%d %B %Y")}\n'
        'Pour e-Inspection CI\nLa Direction Générale'
    )
    run_sign.font.size = Pt(11)
    run_sign.font.bold = True
    run_sign.font.color.rgb = BLEU_ACIER
    run_sign.font.name = 'Calibri'

    # ── Sauvegarde ────────────────────────────────────────────────────────
    filename = 'Offre_Commerciale_eInspection_CI_DGT_2026.docx'
    doc.save(filename)
    print(f'OK  Document genere : {filename}')
    return filename


if __name__ == '__main__':
    generate()

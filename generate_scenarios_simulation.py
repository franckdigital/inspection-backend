"""
generate_scenarios_simulation.py
Genere Scenarios_Simulation_eInspection_CI.docx
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HEX_BLEU   = "1A3A5C"
HEX_ORANGE = "E86C00"
HEX_VERT   = "007A3D"
HEX_ROUGE  = "C0392B"
HEX_GRIS   = "F2F2F2"
HEX_BLANC  = "FFFFFF"
HEX_JAUNE  = "FFF3CD"

def rgb(h):
    return RGBColor(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

def h1(doc, text, color=HEX_BLEU):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(6)
    r = p.add_run(text)
    r.bold = True; r.font.color.rgb = rgb(color); r.font.size = Pt(14)
    return p

def h2(doc, text, color=HEX_ORANGE):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(4)
    r = p.add_run(text)
    r.bold = True; r.font.color.rgb = rgb(color); r.font.size = Pt(12)
    return p

def para(doc, text, bold=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.bold = bold; r.font.size = Pt(10.5)
    return p

def bul(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    r.font.size = Pt(10.5)
    return p

def banner(doc, text, bg=HEX_BLEU, fg=HEX_BLANC):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    cell = tbl.cell(0, 0)
    set_cell_bg(cell, bg)
    cell.paragraphs[0].clear()
    r = cell.paragraphs[0].add_run(text)
    r.bold = True; r.font.color.rgb = rgb(fg); r.font.size = Pt(13)
    cell.paragraphs[0].paragraph_format.space_before = Pt(6)
    cell.paragraphs[0].paragraph_format.space_after  = Pt(6)
    cell.paragraphs[0].paragraph_format.left_indent  = Cm(0.3)
    doc.add_paragraph()

def info_table(doc, rows_data):
    tbl = doc.add_table(rows=len(rows_data), cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, (label, value) in enumerate(rows_data):
        lc = tbl.cell(i, 0); vc = tbl.cell(i, 1)
        set_cell_bg(lc, HEX_GRIS)
        lc.paragraphs[0].clear(); vc.paragraphs[0].clear()
        r = lc.paragraphs[0].add_run(label); r.bold = True; r.font.size = Pt(10)
        r2 = vc.paragraphs[0].add_run(value); r2.font.size = Pt(10)
    doc.add_paragraph()

def data_table(doc, headers, rows, hbg=HEX_BLEU):
    tbl = doc.add_table(rows=1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, h in enumerate(headers):
        c = tbl.cell(0, i); set_cell_bg(c, hbg)
        c.paragraphs[0].clear()
        r = c.paragraphs[0].add_run(h)
        r.bold = True; r.font.color.rgb = rgb(HEX_BLANC); r.font.size = Pt(9.5)
    for idx, row in enumerate(rows):
        tr = tbl.add_row()
        bg = HEX_GRIS if idx % 2 == 0 else HEX_BLANC
        for ci, val in enumerate(row):
            c = tr.cells[ci]; set_cell_bg(c, bg)
            c.paragraphs[0].clear()
            r = c.paragraphs[0].add_run(val); r.font.size = Pt(9.5)
    doc.add_paragraph()

def step_table(doc, steps):
    tbl = doc.add_table(rows=1, cols=4)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, h in enumerate(["#", "Etape", "Role", "Action / Ecran"]):
        c = tbl.cell(0, i); set_cell_bg(c, HEX_BLEU)
        c.paragraphs[0].clear()
        r = c.paragraphs[0].add_run(h)
        r.bold = True; r.font.color.rgb = rgb(HEX_BLANC); r.font.size = Pt(9.5)
    for idx, (step, role, action) in enumerate(steps, 1):
        tr = tbl.add_row()
        bg = HEX_GRIS if idx % 2 == 0 else HEX_BLANC
        for c in tr.cells: set_cell_bg(c, bg)
        tr.cells[0].paragraphs[0].clear(); tr.cells[0].paragraphs[0].add_run(str(idx)).font.size = Pt(9.5)
        tr.cells[1].paragraphs[0].clear(); tr.cells[1].paragraphs[0].add_run(step).font.size = Pt(9.5)
        tr.cells[2].paragraphs[0].clear(); r2=tr.cells[2].paragraphs[0].add_run(role); r2.font.size=Pt(9.5); r2.italic=True
        tr.cells[3].paragraphs[0].clear(); tr.cells[3].paragraphs[0].add_run(action).font.size = Pt(9.5)
    doc.add_paragraph()

def alert(doc, text, t="info"):
    bgs = {"info":"EBF3FB","warning":"FFF3CD","success":"E8F5E9","danger":"FDECEA"}
    fgs = {"info":HEX_BLEU,"warning":"E6AC00","success":HEX_VERT,"danger":HEX_ROUGE}
    tbl = doc.add_table(rows=1, cols=1)
    c = tbl.cell(0, 0); set_cell_bg(c, bgs[t])
    c.paragraphs[0].clear()
    r = c.paragraphs[0].add_run(text)
    r.font.size = Pt(10); r.font.color.rgb = rgb(fgs[t])
    c.paragraphs[0].paragraph_format.left_indent  = Cm(0.3)
    c.paragraphs[0].paragraph_format.space_before = Pt(4)
    c.paragraphs[0].paragraph_format.space_after  = Pt(4)
    doc.add_paragraph()

def hr(doc):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"),"single"); bot.set(qn("w:sz"),"6")
    bot.set(qn("w:space"),"1"); bot.set(qn("w:color"),HEX_ORANGE)
    pBdr.append(bot); pPr.append(pBdr)

# =============================================================================
doc = Document()
for s in doc.sections:
    s.top_margin=Cm(2); s.bottom_margin=Cm(2)
    s.left_margin=Cm(2.5); s.right_margin=Cm(2)

# PAGE DE GARDE
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(60)
r = p.add_run("MINISTERE DE L'EMPLOI ET DE LA PROTECTION SOCIALE")
r.bold=True; r.font.size=Pt(13); r.font.color.rgb=rgb(HEX_BLEU)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Direction Generale du Travail - DGT")
r.bold=True; r.font.size=Pt(12); r.font.color.rgb=rgb(HEX_BLEU)

doc.add_paragraph(); doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("eINSPECTION CI")
r.bold=True; r.font.size=Pt(32); r.font.color.rgb=rgb(HEX_ORANGE)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Plateforme Nationale de Gestion du Travail")
r.bold=True; r.font.size=Pt(16); r.font.color.rgb=rgb(HEX_BLEU)

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("SCENARIOS DE SIMULATION REELS")
r.bold=True; r.font.size=Pt(22); r.font.color.rgb=rgb(HEX_VERT)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("De la plainte jusqu'au Tribunal du Travail")
r.bold=True; r.font.size=Pt(14); r.font.color.rgb=rgb("888888")

doc.add_paragraph(); doc.add_paragraph()

data_table(doc,
    ["Rubrique","Contenu"],
    [
        ["Version","1.0 - Juin 2026"],
        ["Modules couverts","14 modules - 15 scenarios detailles"],
        ["Base legale","Code du Travail CI - Loi n 2015-532 du 20 juillet 2015"],
        ["Usage","Formation, demonstration, recette fonctionnelle"],
    ], hbg=HEX_BLEU
)

doc.add_page_break()

# =============================================================================
# INTRODUCTION
# =============================================================================
h1(doc, "0. INTRODUCTION ET MODE D'EMPLOI")
para(doc, (
    "Ce document presente 15 scenarios de simulation reels pour la plateforme eINSPECTION CI. "
    "Chaque scenario repose sur des situations concretes du droit du travail ivoirien, "
    "avec des acteurs nommes, des donnees chiffrees precises et un parcours pas a pas "
    "sur la plateforme : du depot de plainte jusqu'a la decision judiciaire."
))

h2(doc, "Comptes utilisateurs de test a creer")
data_table(doc,
    ["Nom complet","Email","Role","Mot de passe"],
    [
        ["KOUASSI Jean-Baptiste",   "jb.kouassi@test.ci",        "EMPLOYE",            "Test@2026!"],
        ["Mme KONE Assata",         "assata.kone@test.ci",       "EMPLOYE",            "Test@2026!"],
        ["BAMBA Souleymane",        "sbamba.batibuild@test.ci",  "EMPLOYEUR",          "Test@2026!"],
        ["SEKONGO Awa",             "awa.sekongo@test.ci",       "EMPLOYE_MAISON",     "Test@2026!"],
        ["Famille KOUAME Roger",    "roger.kouame@test.ci",      "EMPLOYEUR",          "Test@2026!"],
        ["Mme DIALLO Aissata",      "diallo.aissata@dgt.ci",     "INSPECTEUR",         "Inspect@2026!"],
        ["M. OUATTARA Fausseni",    "ouattara.f@dgt.ci",         "INSPECTEUR",         "Inspect@2026!"],
        ["M. BAMBA Lassina",        "bamba.lassina@dgt.ci",      "CHEF_INSPECTION",    "Chef@2026!"],
        ["Mme TOURE Nafissatou",    "toure.nafissa@dgt.ci",      "DIRECTEUR_REGIONAL", "Direct@2026!"],
        ["M. KONAN Edmond",         "konan.edmond@dgt.ci",       "DIRECTEUR_GENERAL",  "DG@2026!"],
        ["Admin Systeme",           "admin@einspection.ci",      "ADMIN",              "Admin@2026!"],
    ]
)

h2(doc, "Entreprises a creer dans le systeme")
data_table(doc,
    ["Raison sociale","Secteur","RCCM","Localisation","Effectif"],
    [
        ["AGRO-INDUSTRIES COTE SUD (AGROCIS)", "Agroalimentaire",  "CI-ABJ-2012-B-14532", "Yopougon Zone Ind.", "187"],
        ["BATIBUILD CONSTRUCTION CI",           "BTP / Construction","CI-ABJ-2018-B-09871","Marcory",           "64"],
        ["HOTEL IVOIRE PALACE",                 "Hotellerie",       "CI-ABJ-2009-B-03215", "Plateau",           "210"],
        ["CHIMIVOIRE SARL",                     "Industrie chimique","CI-ABJ-2015-B-11204","Vridi Zone Ind.",   "95"],
        ["PALMAFRIQUE SA",                      "Agriculture",      "CI-SDP-2005-B-00872", "San-Pedro",         "320"],
        ["BCI BANQUE",                          "Banque / Finance",  "CI-ABJ-2001-B-00115","Plateau",           "850"],
        ["TEXTILCI SA",                         "Textile",          "CI-ABJ-2008-B-07643", "Koumassi Zone Ind.","430"],
        ["CIMAF COTE D'IVOIRE",                 "Cimenterie",       "CI-ABJ-2010-B-08812", "Vridi",             "240"],
        ["SITRACOMEX SARL",                     "Import-Export",    "CI-ABJ-2019-B-15001", "Abobo",             "28"],
    ]
)

doc.add_page_break()

# =============================================================================
# PARTIE I - PLAINTES
# =============================================================================
banner(doc, "PARTIE I - MODULE : GESTION DES PLAINTES", bg=HEX_BLEU)

# --- SCENARIO 1 ---
banner(doc, "SCENARIO 1 - Licenciement abusif sans indemnites (AGROCIS)", bg=HEX_ORANGE)

h2(doc, "1.1 Profil des acteurs")
info_table(doc, [
    ("Employe plaignant",  "KOUASSI Jean-Baptiste, 42 ans, technicien de maintenance"),
    ("Anciennete",         "11 ans (embauche le 03/03/2015)"),
    ("Salaire mensuel",    "285 000 FCFA brut"),
    ("Employeur",          "AGRO-INDUSTRIES COTE SUD (AGROCIS) - Zone Industrielle de Yopougon"),
    ("Directeur concerne", "M. KOFFI Herve, Directeur Technique"),
    ("Inspectrice saisie", "Mme DIALLO Aissata - Bureau Yopougon"),
    ("Chef inspection",    "M. BAMBA Lassina"),
])

h2(doc, "1.2 Description des faits")
para(doc, (
    "Le 15 mars 2026, KOUASSI Jean-Baptiste est convoque verbalement par M. KOFFI Herve et "
    "licencie seance tenante pour 'faute grave', apres un desaccord sur les heures supplementaires "
    "de fevrier 2026. Aucune lettre de mise en demeure ni procedure disciplinaire prealable "
    "n'a ete respectee. Aucune indemnite n'a ete versee. "
    "Le preavis de 3 mois (anciennete > 10 ans) a ete ignore."
))

h2(doc, "1.3 Droits violes (Code du Travail CI - Loi 2015-532)")
bul(doc, "Art. 16.1 : absence de convocation ecrite et de procedure disciplinaire prealable")
bul(doc, "Art. 16.7 : motif de licenciement non communique par ecrit dans les delais")
bul(doc, "Art. 18.1 : preavis 3 mois non respecte => indemnite compensatrice = 3 x 285 000 = 855 000 FCFA")
bul(doc, "Art. 18.10 : indemnite de licenciement non versee => 11 x 285 000 x (1/3) = 1 045 000 FCFA")
bul(doc, "Art. 18.12 : certificat de travail non remis dans les 48h")

h2(doc, "1.4 Calcul des droits dus")
data_table(doc,
    ["Element","Calcul","Montant (FCFA)"],
    [
        ["Preavis (3 mois)",              "3 x 285 000",              "855 000"],
        ["Indemnite de licenciement",     "11 x 285 000 x 1/3",       "1 045 000"],
        ["Conges payes restants (18j)",   "285 000 / 26 x 18",        "197 307"],
        ["Dommages et interets (6 mois)", "6 x 285 000",              "1 710 000"],
        ["TOTAL RECLAME",                 "",                          "3 807 307"],
    ], hbg=HEX_ROUGE
)

h2(doc, "1.5 Parcours pas a pas sur la plateforme")
step_table(doc, [
    ("Connexion a la plateforme",    "EMPLOYE (KOUASSI)",      "Accueil => Se connecter => jb.kouassi@test.ci"),
    ("Depot de la plainte",          "EMPLOYE",                "Menu 'Mes plaintes' => 'Deposer une plainte'"),
    ("Saisie du formulaire",         "EMPLOYE",                "Entreprise: AGROCIS | Categorie: LICENCIEMENT | Date: 15/03/2026"),
    ("Description detaillee",        "EMPLOYE",                "Copier les faits du 1.2 dans le champ Description"),
    ("Pieces jointes",               "EMPLOYE",                "Joindre: contrat de travail + bulletins 3 mois + SMS/email"),
    ("Soumission",                   "EMPLOYE",                "Cliquer 'Soumettre' => N numero attribue: PLT-2026-001234"),
    ("Reception et assignation",     "CHEF_INSPECTION (BAMBA)","Tableau de bord => Nouvelle plainte => Assigner a Mme DIALLO"),
    ("Accuse reception",             "INSPECTEUR (DIALLO)",    "Plainte PLT-2026-001234 => 'Prendre en charge'"),
    ("Demande de documents",         "INSPECTEUR",             "Onglet Documents => Demander: registre, bulletins, RI"),
    ("Programmation inspection",     "INSPECTEUR",             "Onglet Inspection => Nouvelle visite => 22/03/2026 09h00 AGROCIS"),
    ("Mise a jour statut",           "INSPECTEUR",             "Statut: EN_INSTRUCTION => MEDIATION_REQUISE"),
    ("Convocation mediation",        "INSPECTEUR",             "Mediation => Nouvelle seance => 29/03/2026 10h00"),
])

h2(doc, "1.6 Donnees de saisie exactes")
info_table(doc, [
    ("Numero plainte (auto)", "PLT-2026-001234"),
    ("Categorie",             "LICENCIEMENT_ABUSIF"),
    ("Priorite",              "HIGH"),
    ("Date des faits",        "15/03/2026"),
    ("Montant reclame",       "3 807 307 FCFA"),
    ("Statut initial",        "SUBMITTED"),
    ("Delai legal",           "30 jours calendaires"),
])

alert(doc, "RESULTAT ATTENDU : Accord en mediation pour 2 850 000 FCFA - payables en 2 versements. Accord signe le 05/04/2026.", "success")
hr(doc)

# --- SCENARIO 2 ---
banner(doc, "SCENARIO 2 - Non-paiement de salaires collectif (BATIBUILD)", bg=HEX_ROUGE)

h2(doc, "2.1 Profil des acteurs")
info_table(doc, [
    ("Employes plaignants",  "8 ouvriers du batiment (macon, carreleur, electricien, peintre)"),
    ("Representant mandate", "TRAORE Moussa, macon chef d'equipe - 5 ans anciennete"),
    ("Salaire moyen",        "95 000 FCFA / mois"),
    ("Employeur",            "BATIBUILD CONSTRUCTION CI - Marcory"),
    ("Gerant",               "M. COULIBALY Adama"),
    ("Inspecteur",           "M. OUATTARA Fausseni - Bureau de Marcory"),
    ("Motif",                "3 mois de salaires impayes : janvier, fevrier, mars 2026"),
])

h2(doc, "2.2 Description des faits")
para(doc, (
    "Depuis janvier 2026, BATIBUILD ne paie plus ses 8 ouvriers de chantier. "
    "Le gerant M. COULIBALY invoque des 'problemes de tresorerie' lies au retard de paiement "
    "d'un marche public. Les ouvriers ont epuise leurs economies. TRAORE Moussa, "
    "mandate par le groupe, depose une plainte collective le 05 avril 2026."
))

h2(doc, "2.3 Droits violes")
bul(doc, "Art. 14.4 CT : le salaire est du a date fixe - tout retard > 8 jours = infraction penale")
bul(doc, "Art. 14.7 CT : obligation de paiement meme en cas de difficultes financieres")
bul(doc, "Art. 74 CT : travail force si retention de salaire prolongee - peine d'emprisonnement possible")

h2(doc, "2.4 Montants en jeu")
data_table(doc,
    ["Ouvrier","Poste","Salaire/mois","Mois impayes","Du"],
    [
        ["TRAORE Moussa",    "Macon chef",  "110 000", "3", "330 000"],
        ["KONE Seydou",      "Macon",       "95 000",  "3", "285 000"],
        ["DIABATE Ibrahim",  "Carreleur",   "98 000",  "3", "294 000"],
        ["YEO Lacina",       "Electricien", "105 000", "3", "315 000"],
        ["DOSSO Hamidou",    "Peintre",     "88 000",  "3", "264 000"],
        ["BAMBA Oumar",      "Macon",       "92 000",  "3", "276 000"],
        ["FOFANA Salia",     "Plombier",    "99 000",  "3", "297 000"],
        ["COULIBALY Sekou",  "Manoeuvre",   "78 000",  "3", "234 000"],
        ["TOTAL",            "",            "",         "",  "2 295 000"],
    ], hbg=HEX_ROUGE
)

h2(doc, "2.5 Parcours plateforme")
step_table(doc, [
    ("Depot plainte collective",  "EMPLOYE (TRAORE)",       "Nouvelle plainte => Type: COLLECTIVE => Joindre mandats des 8 ouvriers"),
    ("Saisie co-plaignants",      "EMPLOYE",                "Section 'Co-plaignants' => Ajouter les 7 autres noms + CNI"),
    ("Assignation urgente",       "CHEF_INSPECTION",        "Priorite: URGENT => Assigner OUATTARA => Delai: 5 jours ouvrables"),
    ("Injonction de payer",       "INSPECTEUR",             "Onglet Injonction => Generer => Delai reponse employeur: 48h"),
    ("Visite inopinee",           "INSPECTEUR",             "Inspection BATIBUILD 08/04/2026 => PV constat => INFRACTION_CONSTATEE"),
    ("Mediation d'urgence",       "INSPECTEUR",             "Mediation => Urgente => 10/04/2026 => Convoquer COULIBALY + TRAORE"),
    ("Non-comparution employeur", "INSPECTEUR",             "Seance 10/04: COULIBALY absent => Cocher employer_no_show => PV carence"),
    ("Saisine tribunal",          "INSPECTEUR",             "Judiciaire => Nouvelle procedure => Joindre PV carence + PV infraction"),
])

alert(doc, "POINT CLE : La non-comparution de l'employeur genere automatiquement un PV de carence et declenche la procedure judiciaire. Tester le module 'Non-comparution employeur'.", "warning")
hr(doc)

# --- SCENARIO 3 ---
banner(doc, "SCENARIO 3 - Harcelement sexuel au travail (Hotel Ivoire Palace)", bg="6C3483")

h2(doc, "3.1 Profil des acteurs")
info_table(doc, [
    ("Employee plaignante", "Mme KONE Assata, 28 ans, receptionniste principale"),
    ("Anciennete",          "3 ans"),
    ("Salaire",             "185 000 FCFA / mois"),
    ("Harceleur presume",   "M. DIABATE Charles, Directeur des operations"),
    ("Employeur",           "HOTEL IVOIRE PALACE - Plateau"),
    ("Inspectrice",         "Mme DIALLO Aissata"),
    ("Type de plainte",     "HARCELEMENT_SEXUEL"),
    ("Preuves",             "SMS, email professionnel, 2 temoins collegues"),
])

h2(doc, "3.2 Description des faits")
para(doc, (
    "De janvier a mars 2026, M. DIABATE Charles a exerce des pressions repetees sur Mme KONE Assata, "
    "lui proposant promotion et prime en echange de faveurs. A son refus, elle a ete retrogradee "
    "au poste d'employee de chambre et ses horaires ont ete modifies unilateralement. "
    "Elle a conserve des captures SMS et une collegue est prete a temoigner."
))

h2(doc, "3.3 Droits violes")
bul(doc, "Art. 4.2 CT : interdiction de tout harcelement moral ou sexuel au travail")
bul(doc, "Art. 16.1 CT : modification unilaterale du contrat (retrogradation) sans accord = licenciement indirect")
bul(doc, "Code Penal CI Art. 356 : harcelement sexuel - peine de 1 a 5 ans + amende")
bul(doc, "Protection renforcee : toute mesure defavorable post-plainte = discrimination presumee")

step_table(doc, [
    ("Connexion confidentielle",  "EMPLOYE (KONE)",         "Nouvelle plainte => Type: HARCELEMENT => Cocher 'Confidentiel'"),
    ("Pieces jointes",            "EMPLOYE",                "Joindre: captures SMS + email => Marquer 'Pieces sensibles'"),
    ("Reception restreinte",      "CHEF_INSPECTION",        "Notification chiffree => Assigner exclusivement a Mme DIALLO"),
    ("Audition employee",         "INSPECTEUR",             "PV audition Mme KONE => 07/04/2026 - Bureaux DGT Plateau"),
    ("Audition direction",        "INSPECTEUR",             "PV audition M. DIABATE separement => 09/04/2026"),
    ("Rapport d'enquete",         "INSPECTEUR",             "Rapport => Conclusion: HARCELEMENT AVERE => Transmission DG"),
    ("Saisine Parquet",           "DIRECTEUR_REGIONAL",     "Valider => Lettre transmission Parquet + ONEF"),
    ("Suivi judiciaire",          "INSPECTEUR",             "Procedure judiciaire => Type: PENAL => Tribunal correctionnel Abidjan"),
])

alert(doc, "TEST SECURITE : Verifier que seuls l'INSPECTEUR assigne et le CHEF_INSPECTION voient cette plainte. Les autres comptes EMPLOYE ne doivent pas y avoir acces.", "info")

doc.add_page_break()

# =============================================================================
# PARTIE II - INSPECTIONS
# =============================================================================
banner(doc, "PARTIE II - MODULE : INSPECTIONS DU TRAVAIL", bg=HEX_BLEU)

# --- SCENARIO 4 ---
banner(doc, "SCENARIO 4 - Conditions de travail dangereuses (CHIMIVOIRE Vridi)", bg=HEX_ROUGE)

h2(doc, "4.1 Contexte")
info_table(doc, [
    ("Entreprise",      "CHIMIVOIRE SARL - Vridi Zone Industrielle"),
    ("Secteur",         "Fabrication produits chimiques (decapants, solvants industriels)"),
    ("Effectif",        "95 salaries dont 34 exposes aux produits chimiques"),
    ("Inspecteur",      "M. OUATTARA Fausseni"),
    ("Declencheur",     "Signalement anonyme + accident corporel leger le 18/03/2026"),
    ("Type inspection", "INOPINEE - Hygiene et Securite"),
    ("Date visite",     "22 mars 2026 a 07h30 (avant ouverture administrative)"),
])

h2(doc, "4.2 Infractions constatees lors de la visite")
data_table(doc,
    ["Ref.","Infraction constatee","Article","Gravite"],
    [
        ["I-01", "Absence EPI (masques, gants) pour 18 postes exposes",       "Art. 42.3 CT",      "CRITIQUE"],
        ["I-02", "Ventilation insuffisante en salle de melange",               "Decret 96-206 Art.8","CRITIQUE"],
        ["I-03", "Fiche de donnees securite absente pour 6 produits",          "Art. 42.1 CT",      "MAJEURE"],
        ["I-04", "Registre accidents de travail non tenu a jour",              "Art. 23.4 CT",      "MAJEURE"],
        ["I-05", "Formation securite non dispensee depuis 2024",               "Art. 42.5 CT",      "MODEREE"],
        ["I-06", "Douches de decontamination hors service (x3)",               "Decret 96-206 Art.15","MAJEURE"],
        ["I-07", "Medecin du travail non designe (entreprise > 50 salaries)",  "Art. 41.2 CT",      "MAJEURE"],
    ]
)

h2(doc, "4.3 Parcours inspection sur la plateforme")
step_table(doc, [
    ("Creation inspection",      "INSPECTEUR",          "Inspections => Nouvelle => Type: INOPINEE => CHIMIVOIRE => 22/03/2026"),
    ("Demarrage sur site",       "INSPECTEUR",          "En cours => Demarrer => Heure debut: 07:30"),
    ("Saisie des constats",      "INSPECTEUR",          "Ajouter infraction x7 => Ref, description, article, gravite, photo"),
    ("Photos jointes",           "INSPECTEUR",          "Joindre: postes sans EPI, salle ventilation, douches HS"),
    ("Cloture visite",           "INSPECTEUR",          "Heure fin: 11:45 => Statut: TERMINEE => Signer PV"),
    ("Mise en demeure",          "INSPECTEUR",          "Generer MED => I-01 & I-02 = 48h | I-03 a I-07 = 15 jours"),
    ("Notification employeur",   "Systeme auto",        "Email + SMS CHIMIVOIRE avec PV + MED"),
    ("Transmission hierarchie",  "INSPECTEUR",          "Envoyer rapport => CHEF_INSPECTION BAMBA pour validation"),
    ("Validation diffusion",     "CHEF_INSPECTION",     "Valider => Copie DIRECTEUR_REGIONAL + CNPS"),
    ("Suivi MED",                "INSPECTEUR",          "J+2: verification terrain EPI | J+15: contre-visite programmee"),
])

alert(doc, "TEST : Verifier qu'une inspection CRITIQUE declenche une notification automatique au CHEF_INSPECTION et DIRECTEUR_REGIONAL (tache Celery).", "warning")
hr(doc)

# --- SCENARIO 5 ---
banner(doc, "SCENARIO 5 - Travail des mineurs (PALMAFRIQUE San-Pedro)", bg="7D6608")

h2(doc, "5.1 Contexte")
info_table(doc, [
    ("Entreprise",    "PALMAFRIQUE SA - Plantation palmier a huile, San-Pedro"),
    ("Signalement",   "ONG DROITS & TRAVAIL CI - 12 mars 2026"),
    ("Inspecteur",    "M. OUATTARA Fausseni (delegation regionale Sud-Comoe)"),
    ("Problematique", "Emploi presume de 15 mineurs (12-16 ans) comme coupeurs de regimes"),
    ("Type",          "INOPINEE - Travail des enfants / Travaux dangereux"),
])

h2(doc, "5.2 Infractions et peines encourues")
bul(doc, "Art. 23.2 CT : age minimum legal = 16 ans travaux legers, 18 ans travaux dangereux")
bul(doc, "Coupage de regimes de palme = TRAVAIL DANGEREUX (coutelas, hauteur, poids) => interdit < 18 ans")
bul(doc, "Convention OIT n 182 : pire forme de travail des enfants - ratifiee par la CI")
bul(doc, "Sanction penale : 1 a 5 ans prison + 500 000 a 5 000 000 FCFA amende (Art. 23.10 CT)")

step_table(doc, [
    ("Inspection programmee",    "CHEF_INSPECTION",   "Nouvelle => Type: INOPINEE => Priorite: URGENTE => Motif: Signalement ONG"),
    ("Mission sur site",         "INSPECTEUR",        "Depart San-Pedro 20/03/2026 => Arrivee plantation 06h00"),
    ("Constat sur le champ",     "INSPECTEUR",        "Photographier mineurs au travail => Verifier registre => Demander CNI"),
    ("Identification mineurs",   "INSPECTEUR",        "Saisir: nom, age, tache, duree journaliere pour chacun des 15 mineurs"),
    ("PV infraction",            "INSPECTEUR",        "PV + liste nominative => 15 chefs d'infraction distincts"),
    ("PV penal",                 "INSPECTEUR",        "Generer PV penal => Transmission Parquet de San-Pedro"),
    ("Rapport urgence",          "INSPECTEUR",        "Rapport => Niveau: CRITIQUE => Diffusion: DGT + Ministere + UNICEF-CI"),
    ("Saisine judiciaire",       "CHEF_INSPECTION",   "Procedure judiciaire => Type: PENAL => Tribunal San-Pedro"),
])

doc.add_page_break()

# =============================================================================
# PARTIE III - MEDIATIONS
# =============================================================================
banner(doc, "PARTIE III - MODULE : MEDIATIONS ET CONCILIATION", bg=HEX_BLEU)

# --- SCENARIO 6 ---
banner(doc, "SCENARIO 6 - Mediation reussie : heures supplementaires (BCI Banque)", bg=HEX_VERT)

h2(doc, "6.1 Contexte")
info_table(doc, [
    ("Plaignants",     "12 agents de back-office - BCI BANQUE, Plateau"),
    ("Representant",   "AHOUA N'Goran, delegue syndical - SYTRACI"),
    ("Sujet",          "Heures supplementaires non remunerees (2024-2025 : 18 mois)"),
    ("Montant total",  "8 640 000 FCFA (moyenne 720 000 FCFA / salarie)"),
    ("Mediatrice",     "Mme DIALLO Aissata"),
    ("Date seance",    "14 avril 2026 - 09h00 - Salle de mediation DGT Plateau"),
    ("Mode",           "PRESENTIAL"),
])

h2(doc, "6.2 Calcul des heures supplementaires dues (Art. 21 CT)")
data_table(doc,
    ["Tranche","Majoration legale","Heures/semaine","Nb semaines","Exemple (salaire 350k)"],
    [
        ["41e a 48e heure/semaine", "+15%", "7h", "78 sem.", "546h x 350k/173h x 1.15 = 1 272 890"],
        ["H. supp. de nuit/dimanche","+50%", "4h", "78 sem.", "312h x 350k/173h x 1.50 = 944 913"],
        ["Total moyen par salarie",  "",     "",    "",        "environ 720 000 FCFA"],
    ]
)

step_table(doc, [
    ("Ouverture seance",       "INSPECTEUR (mediateur)", "Mediations => Seance 14/04/2026 => Statut: ONGOING => Demarrer PV"),
    ("Appel des parties",      "INSPECTEUR",             "Participants => Marquer presents: AHOUA + DRH M. BOGA => attended = true"),
    ("Expose employes",        "INSPECTEUR",             "Saisir declaration employes dans PV => opening_statement"),
    ("Reponse employeur",      "INSPECTEUR",             "DRH BCI reconnat les HS mais conteste montant => employer_statement"),
    ("Proposition accord",     "INSPECTEUR",             "Proposition: 6 400 000 FCFA global (74% du reclame) en 2 versements"),
    ("Contre-proposition",     "INSPECTEUR",             "BCI accepte 6 400 000 en 3 mensualites de 2 133 333 FCFA"),
    ("Accord trouve",          "INSPECTEUR",             "outcome = AGREEMENT => Rediger accord => terms: 30/04, 31/05, 30/06"),
    ("Signature accord",       "INSPECTEUR",             "Accord => Generer PDF => Signature: AHOUA + DRH + Mediateur"),
    ("Cloture",                "INSPECTEUR",             "Seance => Statut: COMPLETED => completed_at = 14/04/2026 12:30"),
])

alert(doc, "RESULTAT : Accord signe - 6 400 000 FCFA en 3 versements. Tester la generation du PDF de l'accord et la signature electronique des 3 parties.", "success")
hr(doc)

# --- SCENARIO 7 ---
banner(doc, "SCENARIO 7 - Non-comparution employeur : PV de carence (SITRACOMEX)", bg=HEX_ROUGE)

h2(doc, "7.1 Contexte")
info_table(doc, [
    ("Plaignant",    "BAMBA Fatogoma, magasinier, 7 ans anciennete"),
    ("Employeur",    "SITRACOMEX SARL (import-export) - Abobo"),
    ("Litige",       "Modification unilaterale lieu de travail (Abidjan => Bouake)"),
    ("Inspectrice",  "Mme DIALLO Aissata"),
    ("Seance 1",     "20/03/2026 - SITRACOMEX absent sans motif"),
    ("Seance 2",     "27/03/2026 - SITRACOMEX absent sans motif (2eme convocation RAR)"),
    ("Consequence",  "Double non-comparution => PV de carence => Procedure judiciaire"),
])

step_table(doc, [
    ("Convocation 1re seance",  "INSPECTEUR",   "Mediation => Nouvelle => 20/03/2026 => Convocations par email + RAR"),
    ("Constat absence J1",      "INSPECTEUR",   "Seance => Appel parties => BAMBA present => SITRACOMEX absent"),
    ("Cocher non-comparution",  "INSPECTEUR",   "employer_no_show = true => no_show_reported_at = 20/03/2026 10h15"),
    ("Generation PV carence 1", "INSPECTEUR",   "Cliquer 'Generer PV de carence' => PDF automatique => Archiver GED"),
    ("2eme convocation",        "INSPECTEUR",   "Nouvelle seance => 27/03/2026 => 2e convocation RAR + notification"),
    ("Constat absence J2",      "INSPECTEUR",   "Seance 27/03 => SITRACOMEX absent a nouveau"),
    ("PV carence definitif",    "INSPECTEUR",   "employer_no_show x2 => PV carence definitif => postpone_count = 2"),
    ("Transmission judiciaire", "CHEF_INSPECTION","Saisine tribunal du travail => Audience sous 15 jours"),
])

alert(doc, "TEST CLE : Verifier que 'pv_carence_generated' passe a True, que le PDF est genere dans mediations/pv_carence/ et que DIRECTEUR_REGIONAL est notifie automatiquement.", "info")

doc.add_page_break()

# =============================================================================
# PARTIE IV - JUDICIAIRE
# =============================================================================
banner(doc, "PARTIE IV - MODULE : PROCEDURES JUDICIAIRES", bg=HEX_BLEU)

# --- SCENARIO 8 ---
banner(doc, "SCENARIO 8 - Licenciement collectif sans plan social (TEXTILCI)", bg="6C3483")

h2(doc, "8.1 Contexte")
info_table(doc, [
    ("Entreprise",    "TEXTILCI SA - Koumassi Zone Industrielle (430 salaries)"),
    ("Faits",         "Licenciement de 120 salaries sans plan social ni consultation IRP"),
    ("Date annonce",  "01 mars 2026 - lettre de licenciement collectif"),
    ("Syndicat",      "DIGNITE-TEXTILE CI - delegue YAPI Konan"),
    ("Inspecteur",    "M. OUATTARA Fausseni"),
    ("Procedure",     "Refere prud'homal + procedure au fond"),
    ("Tribunal",      "Tribunal du Travail d'Abidjan - Section Koumassi"),
])

h2(doc, "8.2 Violations du droit")
bul(doc, "Art. 16.14 CT : licenciement collectif > 10 salaries => obligation de plan social")
bul(doc, "Art. 56 CT : consultation obligatoire du Comite d'Entreprise avant toute decision collective")
bul(doc, "Art. 16.15 CT : notification prealable Inspection du Travail 30 jours avant execution")
bul(doc, "Art. 16.16 CT : priorite de reembauche pendant 2 ans pour les licencies economiques")

step_table(doc, [
    ("Ouverture procedure",   "INSPECTEUR",         "Judiciaire => Nouvelle procedure => Type: LICENCIEMENT_COLLECTIF_ABUSIF"),
    ("Saisie des parties",    "INSPECTEUR",         "Demandeur: DIGNITE-TEXTILE CI | Defendeur: TEXTILCI SA"),
    ("Pieces du dossier",     "INSPECTEUR",         "Joindre: PV inspection, liste 120 licencies, lettre licenciement, PV IRP"),
    ("Requete en refere",     "INSPECTEUR",         "Generer requete => Suspension execution licenciements => Tribunal Abidjan"),
    ("Audience refere",       "INSPECTEUR",         "Audience => 15/03/2026 09h00 => Saisir: juge, resultats plaidoiries"),
    ("Decision refere",       "INSPECTEUR",         "Decision: SUSPENSION licenciements => Statut: DECISION_PROVISOIRE"),
    ("Procedure au fond",     "INSPECTEUR",         "Nouvelle audience => 28/04/2026 => Fond => Nullite des licenciements"),
    ("Decision finale",       "CHEF_INSPECTION",    "Nullite + reintegration 120 OU indemnite x2 => Archiver"),
])

alert(doc, "RESULTAT : Indemnite totale estimee : 120 x 350 000 x 6 mois = 252 000 000 FCFA (Art. 16.12 CT). Ou reintegration forcee.", "warning")
hr(doc)

# --- SCENARIO 9 ---
banner(doc, "SCENARIO 9 - Accident de travail non declare (CIMAF Vridi)", bg=HEX_ROUGE)

h2(doc, "9.1 Contexte")
info_table(doc, [
    ("Victime",        "DIOMANDE Souleymane, 35 ans, operateur four a clinker"),
    ("Employeur",      "CIMAF COTE D'IVOIRE - Usine Vridi"),
    ("Accident",       "05 mars 2026 - brulures 2e degre bras droit - four en maintenance"),
    ("Non-declaration","CIMAF n'a pas declare l'AT a la CNPS dans les 48h reglementaires"),
    ("Inspecteur",     "M. OUATTARA Fausseni"),
    ("Plainte",        "Deposee par DIOMANDE le 10/03/2026 apres refus de prise en charge medicale"),
])

h2(doc, "9.2 Infractions")
bul(doc, "Art. 23.6 CT + Code CNPS : declaration AT obligatoire dans les 48h => amende 50 000 a 500 000 FCFA")
bul(doc, "Art. 23.8 CT : obligation de maintien du salaire pendant arret AT")
bul(doc, "Art. 42.1 CT : obligation de securite lors des operations de maintenance four")
bul(doc, "Code CNPS Art. 36 : prise en charge medicale et indemnisation incapacite temporaire")

step_table(doc, [
    ("Reception plainte",       "CHEF_INSPECTION",  "PLT-2026-001567 => URGENTE => Assigner OUATTARA => Delai 24h"),
    ("Inspection immediate",    "INSPECTEUR",       "Visite CIMAF 11/03/2026 => PV accident => Photos four => Rapport medical"),
    ("Constat non-declaration", "INSPECTEUR",       "Verifier registre CNPS => Confirmation: aucune declaration dans les 48h"),
    ("PV infraction AT",        "INSPECTEUR",       "PV: Non-declaration AT + Non-maintien salaire + Defaut securite"),
    ("Injonction CNPS",         "INSPECTEUR",       "Generer injonction => CIMAF declare AT a CNPS sous 24h"),
    ("Ouverture judiciaire",    "INSPECTEUR",       "Procedure judiciaire => Type: ACCIDENT_TRAVAIL => Demande reparation"),
    ("Expertise medicale",      "INSPECTEUR",       "Joindre rapport medical => Taux IPP estime: 15% => Calcul rente CNPS"),
    ("Audience tribunal",       "INSPECTEUR",       "Tribunal du Travail => 20/04/2026 => Reparation + amende CIMAF"),
])

doc.add_page_break()

# =============================================================================
# PARTIE V - TRAVAIL DOMESTIQUE
# =============================================================================
banner(doc, "PARTIE V - MODULE : TRAVAIL DOMESTIQUE", bg=HEX_BLEU)

# --- SCENARIO 10 ---
banner(doc, "SCENARIO 10 - Contrat, bulletins de paie et conges (Famille KOUAME)", bg=HEX_VERT)

h2(doc, "10.1 Profil")
info_table(doc, [
    ("Employee de maison", "SEKONGO Awa, 24 ans, aide menagere + garde d'enfant"),
    ("Employeur",          "Famille KOUAME Roger & Epouse - Cocody Angre"),
    ("Date embauche",      "01 janvier 2026"),
    ("Taches",             "Menage, cuisine, garde de 2 enfants (5 et 8 ans)"),
    ("Salaire convenu",    "85 000 FCFA / mois (SMIG domestique)"),
    ("Logement",           "Chambre independante fournie par l'employeur"),
    ("Jours travail",      "Lundi au Samedi | Repos: Dimanche"),
])

h2(doc, "10.2 Creation du contrat sur la plateforme")
step_table(doc, [
    ("Connexion",           "EMPLOYEUR (KOUAME)",   "Se connecter => roger.kouame@test.ci"),
    ("Nouveau contrat",     "EMPLOYEUR",            "Travail Domestique => Nouveau contrat => Type: CDI"),
    ("Donnees employee",    "EMPLOYEUR",            "Nom: SEKONGO Awa | CNI: CI-ABJ-2002-12345 | Naissance: 12/05/2002"),
    ("Donnees contrat",     "EMPLOYEUR",            "Debut: 01/01/2026 | Salaire: 85 000 | Poste: AIDE_MENAGERE"),
    ("Avantages en nature", "EMPLOYEUR",            "Logement: OUI (15 000) | Nourriture: OUI (10 000)"),
    ("Generation contrat",  "Systeme",              "Generer PDF contrat => Signature KOUAME + SEKONGO => Archiver GED"),
    ("Enregistrement CNPS", "EMPLOYEUR",            "Exporter fiche immatriculation CNPS => Deposer agence CNPS Cocody"),
])

h2(doc, "10.3 Generation des fiches de paie - Janvier a Juin 2026")
data_table(doc,
    ["Mois","Salaire brut","CNPS salarie (6,3%)","Net a payer","Avantages","Cout total employeur"],
    [
        ["Janvier 2026",  "85 000", "5 355", "79 645", "25 000", "96 028"],
        ["Fevrier 2026",  "85 000", "5 355", "79 645", "25 000", "96 028"],
        ["Mars 2026",     "85 000", "5 355", "79 645", "25 000", "96 028"],
        ["Avril 2026",    "85 000", "5 355", "79 645", "25 000", "96 028"],
        ["Mai 2026",      "85 000", "5 355", "79 645", "25 000", "96 028"],
        ["Juin 2026",     "85 000", "5 355", "79 645", "25 000", "96 028"],
        ["TOTAL 6 mois", "510 000","32 130","477 870","150 000","576 168"],
    ]
)

h2(doc, "10.4 Gestion des conges")
info_table(doc, [
    ("Droit aux conges",    "2,5 jours / mois travaille = 15 jours au bout de 6 mois"),
    ("Conge demande",       "SEKONGO Awa demande 15 jours du 01 au 15 juillet 2026"),
    ("Indemnite conges",    "85 000 x 15 / 26 jours = 49 038 FCFA"),
    ("Statut demande",      "EN_ATTENTE => APPROUVE par famille KOUAME"),
])

step_table(doc, [
    ("Demande conge",    "EMPLOYE_MAISON (SEKONGO)", "Travail Domestique => Mes conges => Nouvelle demande => 01/07 au 15/07/2026"),
    ("Notification",     "Systeme",                   "Email + SMS famille KOUAME => 'Demande de conge en attente'"),
    ("Approbation",      "EMPLOYEUR (KOUAME)",        "Demandes recues => Approuver => Indemnite: 49 038 FCFA"),
    ("Mise a jour",      "Systeme",                   "Solde conges: 0 jours => Prochain cumul: 01/07/2026"),
])

alert(doc, "TEST CELERY : La tache 'generate_monthly_payslips' genere-t-elle automatiquement les bulletins le 1er de chaque mois ? Verifier dans l'admin Celery Beat.", "info")
hr(doc)

# --- SCENARIO 11 ---
banner(doc, "SCENARIO 11 - Conge maternite refuse (Famille TRAORE Marcory)", bg=HEX_ROUGE)

h2(doc, "11.1 Contexte")
info_table(doc, [
    ("Employee",   "COULIBALY Mariam, 26 ans, nourrice et aide cuisiniere"),
    ("Employeur",  "Famille TRAORE Siaka - Marcory Zone 4"),
    ("Salaire",    "75 000 FCFA / mois (SMIG)"),
    ("Situation",  "Enceinte de 7 mois - declaration grossesse le 10/03/2026"),
    ("Probleme",   "La famille TRAORE refuse le conge maternite et menace de licencier"),
    ("Plainte",    "Deposee le 28/03/2026"),
])

h2(doc, "11.2 Droits de la salariee enceinte (Code du Travail CI)")
bul(doc, "Art. 23.1 CT : Conge maternite = 14 semaines (6 avant + 8 apres accouchement) - OBLIGATOIRE")
bul(doc, "Art. 23.2 CT : Interdiction ABSOLUE de licencier une femme enceinte ou en conge maternite")
bul(doc, "Art. 23.3 CT : Maintien du salaire pendant conge maternite - pris en charge CNPS a 100%")
bul(doc, "Art. 23.4 CT : Heure d'allaitement = 1h/jour pendant 15 mois - obligatoire et remuneree")

step_table(doc, [
    ("Depot plainte",       "EMPLOYE_MAISON (COULIBALY)", "Plainte => Type: REFUS_CONGE_MATERNITE => Joindre certificat medical"),
    ("Assignation urgente", "CHEF_INSPECTION",            "URGENT => Assigner DIALLO => Delai 48h (protection femme enceinte)"),
    ("Contact employeur",   "INSPECTEUR",                 "Appel famille TRAORE => Rappel obligations legales => MED verbale"),
    ("MED ecrite",          "INSPECTEUR",                 "MED => Respecter conge maternite sous 48h => Sinon: saisine tribunal"),
    ("Resolution",          "INSPECTEUR",                 "Famille TRAORE accepte => Conge debute 01/04/2026 => Accord signe"),
    ("Suivi CNPS",          "INSPECTEUR",                 "Verifier immatriculation COULIBALY CNPS => Si non immatriculee: injonction"),
])

doc.add_page_break()

# =============================================================================
# PARTIE VI - MODULES TRANSVERSAUX
# =============================================================================
banner(doc, "PARTIE VI - MODULES TRANSVERSAUX (GED, BI, AI, HIERARCHIE)", bg=HEX_BLEU)

# --- SCENARIO 12 ---
banner(doc, "SCENARIO 12 - GED : Gestion electronique des documents", bg="117A65")

h2(doc, "12.1 Contexte")
para(doc, (
    "Ce scenario utilise le dossier du Scenario 1 (KOUASSI vs AGROCIS) pour tester "
    "toutes les fonctionnalites GED : classification, versioning, acces restreint, archivage."
))

h2(doc, "12.2 Documents a creer et classer")
data_table(doc,
    ["Document","Type","Uploader","Acces"],
    [
        ["Contrat de travail KOUASSI (signe 03/03/2015)",  "CONTRAT",           "INSPECTEUR DIALLO",  "INSPECTEUR + CHEF"],
        ["Bulletins de salaire Jan-Mar 2026",               "BULLETINS_PAIE",    "EMPLOYE KOUASSI",    "INSPECTEUR + EMPLOYE"],
        ["Lettre de licenciement du 15/03/2026",           "COURRIER_EMPLOYEUR","EMPLOYE KOUASSI",    "TOUS"],
        ["PV inspection AGROCIS du 22/03/2026",            "PV_INSPECTION",     "INSPECTEUR DIALLO",  "INSPECTEUR + CHEF + DG"],
        ["Convocation mediation du 29/03/2026",            "CONVOCATION",       "Systeme auto",        "TOUS"],
        ["Accord de mediation signe 05/04/2026",           "ACCORD_MEDIATION",  "INSPECTEUR DIALLO",  "TOUS"],
        ["Reglement interieur AGROCIS 2024",               "REGLEMENT_INT.",    "INSPECTEUR DIALLO",  "INSPECTEUR + CHEF"],
    ]
)

step_table(doc, [
    ("Acces GED",            "INSPECTEUR",      "Menu GED => Mes documents => Nouveau document"),
    ("Upload contrat",       "INSPECTEUR",      "Type: CONTRAT | Titre: 'Contrat KOUASSI 2015' | Fichier: contrat.pdf"),
    ("Versioning",           "INSPECTEUR",      "GED => Contrat => Nouvelle version => V2 (avenant 2019) => Comparer"),
    ("Recherche fulltext",   "INSPECTEUR",      "GED => Recherche => 'AGROCIS' => Resultats filtres par dossier"),
    ("Partage",              "INSPECTEUR",      "Document => Acces => Ajouter CHEF_INSPECTION BAMBA => Lecture seule"),
    ("Archivage dossier",    "CHEF_INSPECTION", "Dossier KOUASSI => Archiver => Categorie: DOSSIER_CLOS_ACCORD"),
    ("Verification acces",   "EMPLOYE autre",   "Connexion autre compte => GED => Verifier: document NON visible"),
])
hr(doc)

# --- SCENARIO 13 ---
banner(doc, "SCENARIO 13 - BI & Observatoire : Tableaux de bord et rapports", bg="1A5276")

h2(doc, "13.1 Rapports a generer")
data_table(doc,
    ["Rapport","Role requis","Periode","Indicateur cle"],
    [
        ["Plaintes par secteur d'activite",       "CHEF_INSPECTION",    "T1 2026", "BTP: 42% | Hotellerie: 18%"],
        ["Taux de resolution des mediations",     "DIRECTEUR_REGIONAL", "T1 2026", "73% accord amiable"],
        ["Infractions constatees par type",       "INSPECTEUR",         "Mars 2026","Securite: 45 | Salaires: 32"],
        ["Delai moyen traitement plaintes",       "CHEF_INSPECTION",    "T1 2026", "18 jours (objectif: 30j)"],
        ["Activite par inspecteur",               "CHEF_INSPECTION",    "Mars 2026","DIALLO: 12 | OUATTARA: 9"],
        ["Tableau de bord executif",              "DIRECTEUR_GENERAL",  "T1 2026", "Vue synthetique multi-KPI"],
        ["Export CSV - Plaintes cloturees",       "ADMIN",              "Jan-Jun 2026","Export complet pour audit"],
    ]
)

step_table(doc, [
    ("Connexion DG",           "DIRECTEUR_GENERAL", "Se connecter => konan.edmond@dgt.ci"),
    ("Dashboard executif",     "DIRECTEUR_GENERAL", "Observatoire => Dashboard Executif => Filtrer: T1 2026"),
    ("Rapport infractions",    "CHEF_INSPECTION",   "BI => Rapports => 'Infractions par type' => Mars 2026 => Executer"),
    ("Requete SQL",            "ADMIN",             "BI => Requetes => Nouvelle => Coller SELECT => Executer"),
    ("Test injection SQL",     "ADMIN",             "Saisir 'DELETE FROM...' => Reponse attendue: 'SELECT uniquement autorise'"),
    ("Export donnees",         "ADMIN",             "BI => Exports => Nouveau => Type: PLAINTES => Format: CSV => Lancer"),
    ("Telecharger export",     "ADMIN",             "Exports => PLT-EXPORT-2026 => Statut: COMPLETED => Telecharger CSV"),
])

alert(doc, "TEST SECURITE : Saisir une requete SQL 'DELETE FROM users_user' dans le module BI => Verifier que la plateforme rejette avec 'Seules les requetes SELECT sont autorisees'.", "warning")
hr(doc)

# --- SCENARIO 14 ---
banner(doc, "SCENARIO 14 - Chatbot IA : Assistant juridique du Code du Travail", bg="7D3C98")

h2(doc, "14.1 Questions de test pour le chatbot")
para(doc, "Connectez-vous avec n'importe quel compte => Menu 'Assistant IA' => Poser ces questions une par une.")

data_table(doc,
    ["#","Question posee","Reponse attendue (resume)"],
    [
        ["Q1",
         "Mon employeur ne m'a pas paye depuis 2 mois, que puis-je faire ?",
         "Depot plainte DGT | Art. 14.4 CT | Paiement du sous 8 jours | Saisine tribunal si refus"],
        ["Q2",
         "Quel est le SMIG en Cote d'Ivoire en 2026 ?",
         "75 000 FCFA/mois (decret 2023) | Salaire inferieur = infraction | Reclamation possible sur 3 ans"],
        ["Q3",
         "J'ai ete licencie sans lettre ni indemnite apres 6 ans, quels sont mes droits ?",
         "Preavis: 2 mois | Indemnite: 6 x salaire x 1/3 | Dommages: max 6 mois | Delai plainte: 2 ans"],
        ["Q4",
         "Mon employeur m'oblige a travailler le dimanche sans majoration, est-ce legal ?",
         "Non - Art. 21 CT | Dimanche = repos obligatoire | Si travaille: +50% majoration ou repos compensateur"],
        ["Q5",
         "Combien de jours de conge ai-je apres 2 ans dans la meme entreprise ?",
         "2,5 jours/mois = 30 jours/an | Indemnite = 1/12 salaire annuel | Conge maternite: 14 semaines en plus"],
        ["Q6",
         "Qu'est-ce qu'une faute grave ? Puis-je etre licencie sans preavis ?",
         "Faute grave = vol, violence, abandon poste | Oui sans preavis MAIS procedure disciplinaire OBLIGATOIRE"],
        ["Q7",
         "Mon employeur cotise-t-il a la CNPS ? Comment verifier ?",
         "Obligation tout employeur | Verification: releve CNPS en agence | Defaut = infraction + rattrapage"],
    ]
)
hr(doc)

# --- SCENARIO 15 ---
banner(doc, "SCENARIO 15 - Hierarchie, delegations et notifications systeme", bg="1F618D")

h2(doc, "15.1 Workflow d'escalade hierarchique")
step_table(doc, [
    ("Delegation pouvoir",      "CHEF_INSPECTION (BAMBA)",  "Hierarchie => Delegation => Deleguer a: OUATTARA => 15/04 au 30/04"),
    ("Escalade plainte",        "INSPECTEUR (DIALLO)",      "Plainte PLT-2026-001234 => Escalader => Niveau: CHEF => Motif: non-cooperation"),
    ("Approbation workflow",    "CHEF_INSPECTION (BAMBA)",  "Workflow => Approbations => Valider escalade DIALLO => Notifier DG"),
    ("Escalade vers DG",        "DIRECTEUR_REGIONAL",       "Dossier TEXTILCI => Escalader => Niveau: DIRECTEUR_GENERAL => MAX"),
    ("Test SMS",                "ADMIN",                    "Admin => Notifications => Envoyer test SMS => +225 07 00 00 00"),
    ("Test email",              "ADMIN",                    "Admin => Templates Email => Modifier 'Nouvelle plainte' => Test"),
    ("Historique reassignations","CHEF_INSPECTION",         "Hierarchie => Reassignations => Voir historique par dossier"),
    ("Notifications push",      "ADMIN",                    "Admin => Push => Envoyer notification test => Verifier mobile"),
])

doc.add_page_break()

# =============================================================================
# ANNEXES
# =============================================================================
banner(doc, "ANNEXES", bg=HEX_BLEU)

h1(doc, "A. Recapitulatif des 15 scenarios")
data_table(doc,
    ["N","Scenario","Module principal","Acteur cle","Resultat attendu"],
    [
        ["1",  "Licenciement abusif - AGROCIS",        "Plaintes + Mediation",   "KOUASSI J-B",     "Accord 2 850 000 FCFA"],
        ["2",  "Non-paiement collectif - BATIBUILD",   "Plaintes + Judiciaire",  "TRAORE Moussa",   "PV carence + Tribunal"],
        ["3",  "Harcelement sexuel - Hotel Ivoire",    "Plaintes + Penal",       "KONE Assata",     "Transmission Parquet"],
        ["4",  "Conditions dangereuses - CHIMIVOIRE",  "Inspections",            "OUATTARA F.",     "MED + contre-visite"],
        ["5",  "Travail mineurs - PALMAFRIQUE",        "Inspections + Penal",    "OUATTARA F.",     "PV penal + Parquet"],
        ["6",  "Heures supp. - BCI Banque",            "Mediations",             "AHOUA N'Goran",   "Accord 6 400 000 FCFA"],
        ["7",  "Non-comparution - SITRACOMEX",         "Mediations",             "BAMBA Fatogoma",  "PV carence x2"],
        ["8",  "Licenc. collectif - TEXTILCI",         "Judiciaire",             "YAPI Konan",      "Nullite licenciements"],
        ["9",  "Accident travail - CIMAF",             "Judiciaire",             "DIOMANDE S.",     "Reparation + amende"],
        ["10", "Contrat domestique - Fam. KOUAME",     "Domestique",             "SEKONGO Awa",     "Contrat + 6 bulletins"],
        ["11", "Conge maternite - Fam. TRAORE",        "Domestique + Plaintes",  "COULIBALY Mariam","MED + droits respectes"],
        ["12", "GED dossier AGROCIS",                  "GED",                    "DIALLO A.",       "Archivage complet"],
        ["13", "Tableaux de bord BI",                  "BI + Observatoire",      "KONAN E. (DG)",   "Rapports T1 2026"],
        ["14", "Questions chatbot IA",                 "AI",                     "Tous roles",      "7 reponses juridiques"],
        ["15", "Hierarchie et delegations",            "Hierarchy + Notif.",     "BAMBA L.",        "Workflow complet"],
    ]
)

h1(doc, "B. Articles du Code du Travail CI - Reference rapide")
data_table(doc,
    ["Article","Sujet","Sanction / Consequence"],
    [
        ["Art. 14.4",  "Paiement salaire a date fixe",              "50 000 - 500 000 FCFA amende"],
        ["Art. 16.1",  "Procedure disciplinaire prealable",         "6 mois salaire dommages et interets"],
        ["Art. 16.12", "Licenciement abusif - indemnisation",       "3 a 6 mois salaire minimum"],
        ["Art. 16.14", "Plan social obligatoire (>10 licenciements)","Nullite des licenciements"],
        ["Art. 18.1",  "Preavis selon anciennete",                  "Indemnite compensatrice"],
        ["Art. 18.10", "Indemnite de licenciement",                 "1/3 mois par annee anciennete"],
        ["Art. 21",    "Majoration heures supplementaires",         "+15% a +50% selon tranche"],
        ["Art. 23.1",  "Conge maternite 14 semaines",               "Nullite licenciement femme enceinte"],
        ["Art. 23.2",  "Age minimum 16 ans / 18 ans dangereux",     "500 000 - 5 000 000 FCFA + prison"],
        ["Art. 23.6",  "Declaration AT obligatoire 48h CNPS",       "50 000 - 500 000 FCFA amende"],
        ["Art. 41.2",  "Medecin du travail > 50 salaries",          "Mise en demeure + astreinte"],
        ["Art. 42.3",  "EPI obligatoires postes exposes",           "Suspension activite possible"],
        ["Art. 56",    "Consultation Comite d'Entreprise",          "Nullite decisions sans consultation"],
    ]
)

h1(doc, "C. Donnees chiffrees cles 2026")
data_table(doc,
    ["Parametre","Valeur","Base legale"],
    [
        ["SMIG",                          "75 000 FCFA / mois",       "Decret n 2023-xxx"],
        ["CNPS - Cotisation salarie",     "6,3% du salaire brut",     "Code CNPS CI"],
        ["CNPS - Cotisation employeur",   "14,75% du salaire brut",   "Code CNPS CI"],
        ["Preavis < 1 an",                "8 jours",                  "Art. 18.2 CT"],
        ["Preavis 1 a 5 ans",             "1 mois",                   "Art. 18.2 CT"],
        ["Preavis 5 a 10 ans",            "2 mois",                   "Art. 18.2 CT"],
        ["Preavis > 10 ans",              "3 mois",                   "Art. 18.2 CT"],
        ["Indemnite licenciement",        "1/3 mois / an anciennete", "Art. 18.10 CT"],
        ["Conge annuel",                  "2,5 jours / mois travaille","Art. 25 CT"],
        ["Conge maternite",               "14 semaines (98 jours)",   "Art. 23.1 CT"],
        ["Prescription actions salariales","2 ans",                   "Art. 86 CT"],
        ["H. supp. normales (+15%)",      "41e au 48e heure/semaine", "Art. 21 CT"],
        ["H. supp. de nuit (+50%)",       "Au-dela de la 48e heure",  "Art. 21 CT"],
    ]
)

# Pied de page
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(20)
r = p.add_run(
    "Document confidentiel - Usage interne DGT | eInspection CI 2026 | "
    "Code du Travail CI - Loi n 2015-532 du 20 juillet 2015"
)
r.font.size = Pt(8.5); r.font.color.rgb = rgb("888888"); r.italic = True

output = "Scenarios_Simulation_eInspection_CI.docx"
doc.save(output)
print("Document genere : " + output)

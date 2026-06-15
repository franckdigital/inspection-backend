"""
generate_cas_usage.py
Genere CasUsage_DeuxEmployes_eInspection.docx
Scenario bout en bout : employe de maison (salaire) vs employe entreprise (harcelement)
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Couleurs
BLEU    = "1A3A5C"
ORANGE  = "E86C00"
VERT    = "007A3D"
ROUGE   = "C0392B"
VIOLET  = "6C3483"
GRIS    = "F2F2F2"
GRIS_M  = "D0D0D0"
BLANC   = "FFFFFF"
JAUNE   = "FFF8DC"
CYAN    = "1A6A7C"

# Couleurs scenario A et B
COL_A = "0D6E6E"   # teal fonce
COL_B = "7B2D8B"   # violet

def rgb(h):
    return RGBColor(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

def set_cell_bg(cell, h):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), h)
    tcPr.append(shd)

def set_col_width(cell, cm):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcW = OxmlElement("w:tcW")
    tcW.set(qn("w:w"), str(int(cm * 567)))
    tcW.set(qn("w:type"), "dxa")
    tcPr.append(tcW)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def banner(doc, text, bg=BLEU, fg=BLANC, size=13):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    c = tbl.cell(0, 0); set_cell_bg(c, bg)
    c.paragraphs[0].clear()
    r = c.paragraphs[0].add_run(text)
    r.bold=True; r.font.color.rgb=rgb(fg); r.font.size=Pt(size)
    c.paragraphs[0].paragraph_format.space_before = Pt(7)
    c.paragraphs[0].paragraph_format.space_after  = Pt(7)
    c.paragraphs[0].paragraph_format.left_indent  = Cm(0.4)
    doc.add_paragraph()

def etape_banner(doc, num, text, color):
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    num_cell = tbl.cell(0, 0); set_cell_bg(num_cell, color)
    txt_cell = tbl.cell(0, 1); set_cell_bg(txt_cell, GRIS)
    num_cell.paragraphs[0].clear()
    r = num_cell.paragraphs[0].add_run(num)
    r.bold=True; r.font.color.rgb=rgb(BLANC); r.font.size=Pt(14)
    num_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    num_cell.paragraphs[0].paragraph_format.space_before = Pt(4)
    num_cell.paragraphs[0].paragraph_format.space_after  = Pt(4)
    set_col_width(num_cell, 1.5)
    txt_cell.paragraphs[0].clear()
    r2 = txt_cell.paragraphs[0].add_run(text)
    r2.bold=True; r2.font.color.rgb=rgb(color); r2.font.size=Pt(12)
    txt_cell.paragraphs[0].paragraph_format.space_before = Pt(4)
    txt_cell.paragraphs[0].paragraph_format.space_after  = Pt(4)
    txt_cell.paragraphs[0].paragraph_format.left_indent  = Cm(0.3)
    doc.add_paragraph()

def h2(doc, text, color=ORANGE):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(4)
    r = p.add_run(text)
    r.bold=True; r.font.color.rgb=rgb(color); r.font.size=Pt(11)

def para(doc, text, bold=False, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.bold=bold; r.font.size=Pt(10.5)
    if color: r.font.color.rgb=rgb(color)

def bul(doc, text, color=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Cm(0.5)
    r = p.add_run(text)
    r.font.size=Pt(10.5)
    if color: r.font.color.rgb=rgb(color)

# Table champ => valeur (formulaire)
def form_table(doc, rows, title=None, color=BLEU):
    if title:
        h2(doc, title, color)
    tbl = doc.add_table(rows=1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    hdrs = ["Champ / Label", "Valeur a saisir", "Type"]
    wids = [5.0, 8.5, 2.5]
    for i, h in enumerate(hdrs):
        c = tbl.cell(0, i); set_cell_bg(c, color); set_col_width(c, wids[i])
        c.paragraphs[0].clear()
        r = c.paragraphs[0].add_run(h)
        r.bold=True; r.font.color.rgb=rgb(BLANC); r.font.size=Pt(9.5)
    for idx, row in enumerate(rows):
        tr = tbl.add_row()
        bg = GRIS if idx % 2 == 0 else BLANC
        field, val, typ = row[0], row[1], row[2] if len(row) > 2 else ""
        cells = tr.cells
        for c in cells: set_cell_bg(c, bg)
        cells[0].paragraphs[0].clear(); set_col_width(cells[0], wids[0])
        r = cells[0].paragraphs[0].add_run(field); r.bold=True; r.font.size=Pt(9.5)
        cells[1].paragraphs[0].clear(); set_col_width(cells[1], wids[1])
        r2 = cells[1].paragraphs[0].add_run(val)
        r2.font.size=Pt(9.5); r2.font.color.rgb=rgb(ROUGE)
        cells[2].paragraphs[0].clear(); set_col_width(cells[2], wids[2])
        r3 = cells[2].paragraphs[0].add_run(typ); r3.font.size=Pt(9); r3.italic=True
    doc.add_paragraph()

def info_table(doc, rows, c1=4.0, c2=12.0):
    tbl = doc.add_table(rows=len(rows), cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, (k, v) in enumerate(rows):
        lc = tbl.cell(i,0); vc = tbl.cell(i,1)
        set_cell_bg(lc, GRIS); set_col_width(lc, c1); set_col_width(vc, c2)
        lc.paragraphs[0].clear(); vc.paragraphs[0].clear()
        r = lc.paragraphs[0].add_run(k); r.bold=True; r.font.size=Pt(10)
        r2 = vc.paragraphs[0].add_run(v); r2.font.size=Pt(10)
    doc.add_paragraph()

def data_table(doc, hdrs, rows, hbg=BLEU, wids=None):
    tbl = doc.add_table(rows=1, cols=len(hdrs))
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, h in enumerate(hdrs):
        c = tbl.cell(0, i); set_cell_bg(c, hbg)
        if wids: set_col_width(c, wids[i])
        c.paragraphs[0].clear()
        r = c.paragraphs[0].add_run(h)
        r.bold=True; r.font.color.rgb=rgb(BLANC); r.font.size=Pt(9.5)
    for idx, row in enumerate(rows):
        tr = tbl.add_row()
        bg = GRIS if idx % 2 == 0 else BLANC
        for ci, val in enumerate(row):
            c = tr.cells[ci]; set_cell_bg(c, bg)
            if wids: set_col_width(c, wids[ci])
            c.paragraphs[0].clear()
            r = c.paragraphs[0].add_run(val); r.font.size=Pt(9.5)
    doc.add_paragraph()

def alert(doc, text, t="info"):
    bgs = {"info":"EBF3FB","warning":"FFF3CD","success":"E8F5E9","danger":"FDECEA","note":"F4F0FB"}
    fgs = {"info":BLEU,"warning":"8A6000","success":VERT,"danger":ROUGE,"note":VIOLET}
    icons= {"info":"INFO","warning":"ATTENTION","success":"OK","danger":"ERREUR","note":"NOTE"}
    tbl = doc.add_table(rows=1, cols=1)
    c = tbl.cell(0, 0); set_cell_bg(c, bgs[t])
    c.paragraphs[0].clear()
    r = c.paragraphs[0].add_run(icons[t] + " : " + text)
    r.font.size=Pt(10); r.font.color.rgb=rgb(fgs[t])
    c.paragraphs[0].paragraph_format.left_indent  = Cm(0.4)
    c.paragraphs[0].paragraph_format.space_before = Pt(5)
    c.paragraphs[0].paragraph_format.space_after  = Pt(5)
    doc.add_paragraph()

def action_box(doc, text, color=VERT):
    tbl = doc.add_table(rows=1, cols=1)
    c = tbl.cell(0, 0); set_cell_bg(c, "E8F8EF" if color == VERT else "FEF9E7")
    c.paragraphs[0].clear()
    r = c.paragraphs[0].add_run(">>> ACTION : " + text)
    r.bold=True; r.font.size=Pt(10); r.font.color.rgb=rgb(color)
    c.paragraphs[0].paragraph_format.left_indent  = Cm(0.4)
    c.paragraphs[0].paragraph_format.space_before = Pt(4)
    c.paragraphs[0].paragraph_format.space_after  = Pt(4)
    doc.add_paragraph()

def result_box(doc, text):
    tbl = doc.add_table(rows=1, cols=1)
    c = tbl.cell(0, 0); set_cell_bg(c, "EAF6FF")
    c.paragraphs[0].clear()
    r = c.paragraphs[0].add_run("RESULTAT SYSTEME : " + text)
    r.bold=True; r.font.size=Pt(10); r.font.color.rgb=rgb(CYAN)
    c.paragraphs[0].paragraph_format.left_indent  = Cm(0.4)
    c.paragraphs[0].paragraph_format.space_before = Pt(4)
    c.paragraphs[0].paragraph_format.space_after  = Pt(4)
    doc.add_paragraph()

def hr(doc, color=ORANGE):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"),"single"); bot.set(qn("w:sz"),"6")
    bot.set(qn("w:space"),"1"); bot.set(qn("w:color"),color)
    pBdr.append(bot); pPr.append(pBdr)

# =============================================================================
# DOCUMENT
# =============================================================================
doc = Document()
for s in doc.sections:
    s.top_margin=Cm(2); s.bottom_margin=Cm(2)
    s.left_margin=Cm(2.5); s.right_margin=Cm(2)

# ─── PAGE DE GARDE ────────────────────────────────────────────────────────────
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(50)
r = p.add_run("eINSPECTION CI")
r.bold=True; r.font.size=Pt(34); r.font.color.rgb=rgb(ORANGE)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Plateforme Nationale de Gestion du Travail")
r.bold=True; r.font.size=Pt(14); r.font.color.rgb=rgb(BLEU)

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("CAS D'USAGE COMPLET")
r.bold=True; r.font.size=Pt(24); r.font.color.rgb=rgb(BLEU)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Deux employes, deux litiges, deux denouements")
r.bold=True; r.font.size=Pt(15); r.font.color.rgb=rgb("555555")

doc.add_paragraph()
doc.add_paragraph()

# Vignettes des deux scenarios
tbl = doc.add_table(rows=1, cols=2)
tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

ca = tbl.cell(0, 0); set_cell_bg(ca, COL_A)
ca.paragraphs[0].clear()
ra = ca.paragraphs[0].add_run("SCENARIO A\nEmploye de maison\nNon-paiement de salaire\nEmployeur : COOPERE")
ra.bold=True; ra.font.color.rgb=rgb(BLANC); ra.font.size=Pt(12)
ca.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
ca.paragraphs[0].paragraph_format.space_before = Pt(14)
ca.paragraphs[0].paragraph_format.space_after  = Pt(14)

cb = tbl.cell(0, 1); set_cell_bg(cb, COL_B)
cb.paragraphs[0].clear()
rb = cb.paragraphs[0].add_run("SCENARIO B\nEmploye d'entreprise\nHarcelement moral\nEmployeur : REFUSE")
rb.bold=True; rb.font.color.rgb=rgb(BLANC); rb.font.size=Pt(12)
cb.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
cb.paragraphs[0].paragraph_format.space_before = Pt(14)
cb.paragraphs[0].paragraph_format.space_after  = Pt(14)

doc.add_paragraph()
data_table(doc,
    ["","Scenario A","Scenario B"],
    [
        ["Type employe",    "EMPLOYE_MAISON",           "EMPLOYE"],
        ["Motif plainte",   "Non-paiement 2 mois",      "Harcelement moral"],
        ["Employeur",       "Mme KONAN Adjoua (famille)","CITRADE SARL (M. ESSIS)"],
        ["Reaction conv.",  "ACCEPTE et se presente",   "REFUSE - absent x2"],
        ["Issue",           "Accord amiable en mediation","PV carence => Tribunal"],
    ], hbg=BLEU
)

doc.add_page_break()

# ─── PRESENTATION DES ACTEURS ─────────────────────────────────────────────────
banner(doc, "ACTEURS DU CAS D'USAGE", bg=BLEU)

h2(doc, "Employes", color=COL_A)
data_table(doc,
    ["Role","Nom complet","Email","Mot de passe","Profil"],
    [
        ["EMPLOYE_MAISON", "COULIBALY Fatou",  "fatou.coulibaly@test.ci",  "Test@2026!", "Aide menagere, 32 ans, Cocody"],
        ["EMPLOYE",        "BAMBA Awa",         "awa.bamba@test.ci",        "Test@2026!", "Assist. commerciale, 26 ans, Plateau"],
    ], hbg=COL_A
)

h2(doc, "Employeurs", color=COL_B)
data_table(doc,
    ["Role","Nom / Entite","Email","Mot de passe","Profil"],
    [
        ["EMPLOYEUR","Mme KONAN Adjoua (famille)","adjoua.konan@test.ci","Test@2026!", "Particulier - Cocody Riviera 3"],
        ["EMPLOYEUR","CITRADE SARL - M. ESSIS Patrice","essis.citrade@test.ci","Test@2026!","Societe commerce import/export - Plateau"],
    ], hbg=COL_B
)

h2(doc, "Inspecteurs et hierarchie", color=BLEU)
data_table(doc,
    ["Role","Nom complet","Email","Mot de passe"],
    [
        ["INSPECTEUR",         "Mme DIALLO Aissata",    "diallo.aissata@dgt.ci",   "Inspect@2026!"],
        ["INSPECTEUR",         "M. OUATTARA Fausseni",  "ouattara.f@dgt.ci",       "Inspect@2026!"],
        ["CHEF_INSPECTION",    "M. BAMBA Lassina",      "bamba.lassina@dgt.ci",    "Chef@2026!"],
        ["DIRECTEUR_REGIONAL", "Mme TOURE Nafissatou",  "toure.nafissa@dgt.ci",    "Direct@2026!"],
    ], hbg=BLEU
)

h2(doc, "Entreprise a creer pour Scenario B", color=COL_B)
info_table(doc, [
    ("Raison sociale",  "CITRADE SARL"),
    ("Secteur",         "Commerce import-export"),
    ("RCCM",            "CI-ABJ-2022-B-18904"),
    ("Adresse",         "Plateau - Immeuble Woodin Center, 3e etage"),
    ("Telephone",       "+225 27 22 44 55 00"),
    ("Effectif",        "23 salaries"),
    ("NCC patronale",   "CI-PAT-2022-45871"),
])

doc.add_page_break()

# ─── CHRONOLOGIE ──────────────────────────────────────────────────────────────
banner(doc, "CHRONOLOGIE DES EVENEMENTS", bg=BLEU)
data_table(doc,
    ["Date","Heure","Scenario","Evenement"],
    [
        ["Lundi 06/04/2026",    "08h30", "A",    "COULIBALY Fatou depose sa plainte (non-paiement)"],
        ["Lundi 06/04/2026",    "09h15", "B",    "BAMBA Awa depose sa plainte (harcelement)"],
        ["Lundi 06/04/2026",    "10h00", "A+B",  "Chef inspection BAMBA reçoit les 2 plaintes et les assigne"],
        ["Lundi 06/04/2026",    "10h30", "A+B",  "Mme DIALLO prend en charge les 2 dossiers"],
        ["Mercredi 08/04/2026", "09h00", "A",    "Mme DIALLO contacte Mme KONAN (convocation acceptee)"],
        ["Mercredi 08/04/2026", "10h00", "B",    "Mme DIALLO contacte CITRADE (1re convocation - pas de reponse)"],
        ["Lundi 13/04/2026",    "09h00", "A",    "Seance de mediation - Mme KONAN PRESENTE"],
        ["Lundi 13/04/2026",    "09h00", "B",    "1re seance mediation - CITRADE ABSENT"],
        ["Vendredi 17/04/2026", "11h00", "B",    "2e convocation CITRADE (lettre RAR + email)"],
        ["Lundi 20/04/2026",    "09h00", "B",    "2e seance mediation - CITRADE ABSENT x2 => PV carence"],
        ["Lundi 13/04/2026",    "11h30", "A",    "Accord de mediation signe : 160 000 FCFA + engagement"],
        ["Mercredi 22/04/2026", "08h00", "B",    "Saisine tribunal du travail - Dossier transmis"],
        ["Jeudi 07/05/2026",    "09h00", "B",    "Audience tribunal - BAMBA Awa vs CITRADE SARL"],
    ]
)

doc.add_page_break()

# =============================================================================
# SCENARIO A
# =============================================================================
banner(doc, "SCENARIO A  --  COULIBALY Fatou  --  Employe de maison  --  Non-paiement de salaire", bg=COL_A, size=12)

para(doc, (
    "Mme KONAN Adjoua emploie COULIBALY Fatou comme aide menagere depuis le 01 septembre 2024. "
    "Le salaire mensuel convenu est de 80 000 FCFA. Les mois de fevrier et mars 2026 n'ont pas ete payes. "
    "Soit un total de 160 000 FCFA dus. Fatou depose une plainte le 06 avril 2026."
))

# ── ETAPE A1 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "A1", "CONNEXION ET DEPOT DE PLAINTE (Employe de maison)", COL_A)

h2(doc, "Ecran : Page d'accueil => Se connecter", color=COL_A)
form_table(doc, [
    ("Adresse email",     "fatou.coulibaly@test.ci",  "Texte"),
    ("Mot de passe",      "Test@2026!",                "Mot de passe"),
], color=COL_A)
action_box(doc, "Cliquer le bouton 'Se connecter'")
result_box(doc, "Redirection vers le tableau de bord EMPLOYE_MAISON. Menu lateral affiche : Mes plaintes, Mon contrat, Mes bulletins de paie, Mes conges.")

h2(doc, "Ecran : Mes plaintes => Nouvelle plainte", color=COL_A)
action_box(doc, "Cliquer 'Mes plaintes' dans le menu => Cliquer le bouton '+ Deposer une plainte'")

h2(doc, "Formulaire de plainte - Section 1 : Identification de l'employeur", color=COL_A)
form_table(doc, [
    ("Type d'employeur",      "PARTICULIER / EMPLOYEUR MAISON",               "Liste deroulante"),
    ("Nom de l'employeur",    "KONAN Adjoua",                                  "Texte"),
    ("Prenom",                "Adjoua",                                        "Texte"),
    ("Adresse employeur",     "Cocody Riviera 3, Rue des Jardins, Villa n 12", "Texte"),
    ("Telephone employeur",   "+225 07 88 44 21 03",                           "Texte"),
    ("Email employeur",       "adjoua.konan@test.ci",                          "Texte"),
], title="Section 1 : Identification de l'employeur", color=COL_A)

h2(doc, "Formulaire de plainte - Section 2 : Nature du litige", color=COL_A)
form_table(doc, [
    ("Categorie de plainte",  "NON_PAIEMENT_SALAIRE",            "Liste deroulante"),
    ("Date du premier fait",  "28/02/2026",                      "Date (fin fevrier)"),
    ("Date du dernier fait",  "31/03/2026",                      "Date (fin mars)"),
    ("Priorite estimee",      "HIGH",                            "Liste deroulante"),
    ("Montant reclame (FCFA)","160 000",                         "Nombre"),
], title="Section 2 : Nature du litige", color=COL_A)

h2(doc, "Formulaire de plainte - Section 3 : Description detaillee", color=COL_A)
para(doc, "Copier exactement ce texte dans le champ 'Description des faits' :", bold=True, color=COL_A)
tbl = doc.add_table(rows=1, cols=1)
c = tbl.cell(0, 0); set_cell_bg(c, "F0FFF4")
c.paragraphs[0].clear()
txt = (
    "Je suis employe de maison au domicile de Mme KONAN Adjoua depuis le 01 septembre 2024. "
    "Mon salaire mensuel est de 80 000 FCFA. "
    "Mme KONAN ne m'a pas paye les mois de fevrier 2026 et mars 2026, soit 160 000 FCFA que je reclame. "
    "Malgre mes demandes orales repetees (le 05 mars, le 20 mars et le 02 avril 2026), "
    "Mme KONAN repousse toujours le paiement en invoquant des difficultes financieres. "
    "Je n'ai pas de contrat de travail ecrit mais j'ai des reçus de salaire pour les mois precedents. "
    "Je n'ai aucune autre source de revenus et je suis en grande difficulte financiere."
)
r = c.paragraphs[0].add_run(txt)
r.font.size=Pt(10.5); r.font.color.rgb=rgb("1A6A2A")
c.paragraphs[0].paragraph_format.left_indent  = Cm(0.4)
c.paragraphs[0].paragraph_format.space_before = Pt(6)
c.paragraphs[0].paragraph_format.space_after  = Pt(6)
doc.add_paragraph()

h2(doc, "Formulaire de plainte - Section 4 : Pieces jointes", color=COL_A)
form_table(doc, [
    ("Piece 1 : Reçus de salaire",          "Joindre photo ou scan des reçus mois de dec 2025 et jan 2026", "Fichier PDF/JPG"),
    ("Piece 2 : Capture SMS/WhatsApp",      "Joindre captures d'ecran des demandes de paiement non abouties","Fichier JPG/PNG"),
    ("Piece 3 : Piece d'identite CNI",      "CNI COULIBALY Fatou - Recto/Verso",                             "Fichier JPG/PDF"),
    ("Piece 4 : Contrat (si existant)",     "Laisser vide si pas de contrat ecrit",                          "Optionnel"),
], color=COL_A)
action_box(doc, "Cliquer 'Soumettre la plainte' => Confirmer dans la boite de dialogue : 'Oui, soumettre'")
result_box(doc, "Numero attribue : PLT-2026-A-000456 | Statut : SUBMITTED | Email de confirmation envoye a fatou.coulibaly@test.ci | Notification interne au Chef inspection BAMBA")

# ── ETAPE A2 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "A2", "RECEPTION ET ASSIGNATION PAR LE CHEF INSPECTION", COL_A)

h2(doc, "Connexion Chef Inspection", color=COL_A)
form_table(doc, [
    ("Email",       "bamba.lassina@dgt.ci", "Texte"),
    ("Mot de passe","Chef@2026!",           "Mot de passe"),
], color=COL_A)
action_box(doc, "Se connecter => Tableau de bord CHEF_INSPECTION")
result_box(doc, "Notification visible : '2 nouvelles plaintes en attente d'assignation' (PLT-2026-A-000456 et PLT-2026-B-000457)")

h2(doc, "Ecran : Liste des plaintes => PLT-2026-A-000456", color=COL_A)
action_box(doc, "Cliquer sur PLT-2026-A-000456 pour ouvrir le detail")
para(doc, "Le Chef inspection voit le resume de la plainte et doit l'assigner a un inspecteur.", bold=False)

h2(doc, "Formulaire d'assignation", color=COL_A)
form_table(doc, [
    ("Inspecteur assigne",  "DIALLO Aissata",       "Liste deroulante (inspecteurs disponibles)"),
    ("Priorite",            "HIGH",                  "Liste deroulante"),
    ("Date limite de traitement","06/05/2026",       "Date (30 jours)"),
    ("Note interne",        "Plainte employe de maison - Non-paiement 2 mois. Contacter l'employeur rapidement. Mme KONAN joignable au +225 07 88 44 21 03.", "Texte long"),
], color=COL_A)
action_box(doc, "Cliquer 'Assigner et notifier' => Bouton vert")
result_box(doc, "Statut plainte => EN_INSTRUCTION | Email envoye a Mme DIALLO avec le dossier | SMS a COULIBALY Fatou : 'Votre plainte PLT-2026-A-000456 a ete prise en charge par Mme DIALLO Aissata, Inspectrice du Travail'")

# ── ETAPE A3 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "A3", "PRISE EN CHARGE PAR L'INSPECTRICE - CONTACT EMPLOYEUR", COL_A)

h2(doc, "Connexion Inspectrice", color=COL_A)
form_table(doc, [
    ("Email",       "diallo.aissata@dgt.ci", "Texte"),
    ("Mot de passe","Inspect@2026!",          "Mot de passe"),
], color=COL_A)

h2(doc, "Ecran : Mon tableau de bord => PLT-2026-A-000456", color=COL_A)
action_box(doc, "Cliquer sur la plainte => Onglet 'Actions' => Cliquer 'Prendre en charge officiellement'")
result_box(doc, "Statut : EN_INSTRUCTION | Date prise en charge : 06/04/2026 10h30 enregistree automatiquement")

h2(doc, "Ajout d'une note de contact (journal du dossier)", color=COL_A)
form_table(doc, [
    ("Type de note",  "CONTACT_TELEPHONE",                                                   "Liste"),
    ("Date / Heure",  "08/04/2026 09h00",                                                    "Date-heure"),
    ("Destinataire",  "Mme KONAN Adjoua (employeur)",                                        "Texte"),
    ("Compte rendu",  "Appel telephone effectue. Mme KONAN reconnait la dette de 160 000 FCFA (2 mois). Elle accepte la convocation a une seance de mediation le lundi 13/04/2026 a 09h00 au bureau DGT Cocody. Elle prend note des coordonnees.", "Texte long"),
], color=COL_A)
action_box(doc, "Cliquer 'Enregistrer la note'")

h2(doc, "Generation de la convocation officielle", color=COL_A)
action_box(doc, "Onglet 'Mediation' => Cliquer 'Nouvelle seance de mediation'")
form_table(doc, [
    ("Date de la seance",    "13/04/2026",                                   "Date"),
    ("Heure",                "09h00",                                        "Heure"),
    ("Type de seance",       "PRESENTIAL",                                   "Liste"),
    ("Lieu",                 "DGT Cocody - Salle de Mediation - 1er etage", "Texte"),
    ("Mediateur",            "DIALLO Aissata (moi-meme)",                   "Auto-rempli"),
    ("Participant 1",        "COULIBALY Fatou - EMPLOYE - fatou.coulibaly@test.ci",  "Ajouter participant"),
    ("Participant 2",        "KONAN Adjoua - EMPLOYEUR - adjoua.konan@test.ci",      "Ajouter participant"),
    ("Objet de la convocation","Tentative de conciliation - Non-paiement de salaire 2 mois (160 000 FCFA) - Plainte PLT-2026-A-000456","Texte long"),
], color=COL_A)
action_box(doc, "Cliquer 'Creer la seance et envoyer les convocations'")
result_box(doc, "Convocations envoyees par email+SMS a COULIBALY Fatou et KONAN Adjoua | acknowledgment_token genere pour chaque participant | Statut seance : SCHEDULED")

alert(doc, "Mme KONAN ouvre son email, clique sur le lien de confirmation de la convocation. Le systeme enregistre acknowledged_at = 08/04/2026 14h22 pour Mme KONAN.", "success")

# ── ETAPE A4 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "A4", "SEANCE DE MEDIATION - EMPLOYEUR PRESENT ET COOPERATIF", COL_A)

h2(doc, "Le 13 avril 2026 a 09h00 - Salle de mediation DGT Cocody", color=COL_A)
para(doc, "L'inspectrice DIALLO ouvre la seance. Les deux parties sont presentes. Elle demarre la seance sur la plateforme.")

h2(doc, "Ecran : Mediations => MED-2026-000123 => Demarrer la seance", color=COL_A)
action_box(doc, "Cliquer 'Demarrer la seance' => Statut passe a ONGOING | Heure debut enregistree : 09h07")

h2(doc, "Appel des participants - Marquer les presences", color=COL_A)
form_table(doc, [
    ("COULIBALY Fatou",  "Cocher 'Presente' => attended = true",     "Case a cocher"),
    ("KONAN Adjoua",     "Cocher 'Presente' => attended = true",     "Case a cocher"),
], color=COL_A)
action_box(doc, "Cliquer 'Confirmer les presences'")

h2(doc, "Redaction du Proces-Verbal de mediation", color=COL_A)

para(doc, "Champ : Declaration d'ouverture (ouverture formelle de seance) :", bold=True, color=COL_A)
tbl = doc.add_table(rows=1, cols=1); c = tbl.cell(0,0); set_cell_bg(c,"F0FFF4")
c.paragraphs[0].clear()
r = c.paragraphs[0].add_run(
    "Je, Mme DIALLO Aissata, Inspectrice du Travail, declare ouverte la seance de conciliation "
    "en date du 13 avril 2026 a 09h07, relative a la plainte PLT-2026-A-000456 deposee par "
    "Mme COULIBALY Fatou contre Mme KONAN Adjoua pour non-paiement de salaire. "
    "Les deux parties sont presentes. Je rappelle que cette seance est une tentative amiable "
    "et que les declarations des parties restent confidentielles."
)
r.font.size=Pt(10); r.font.color.rgb=rgb("1A6A2A")
c.paragraphs[0].paragraph_format.left_indent=Cm(0.4)
c.paragraphs[0].paragraph_format.space_before=Pt(5)
c.paragraphs[0].paragraph_format.space_after=Pt(5)
doc.add_paragraph()

para(doc, "Champ : Declaration de l'employe :", bold=True, color=COL_A)
tbl = doc.add_table(rows=1, cols=1); c = tbl.cell(0,0); set_cell_bg(c,"F0FFF4")
c.paragraphs[0].clear()
r = c.paragraphs[0].add_run(
    "Je confirme travailler chez Mme KONAN depuis le 01 septembre 2024 comme aide menagere. "
    "Mon salaire est de 80 000 FCFA par mois. Je n'ai pas reçu les salaires de fevrier et mars 2026. "
    "J'ai demande plusieurs fois le paiement mais en vain. Je reclame 160 000 FCFA."
)
r.font.size=Pt(10); r.font.color.rgb=rgb("1A6A2A")
c.paragraphs[0].paragraph_format.left_indent=Cm(0.4)
c.paragraphs[0].paragraph_format.space_before=Pt(5)
c.paragraphs[0].paragraph_format.space_after=Pt(5)
doc.add_paragraph()

para(doc, "Champ : Declaration de l'employeur :", bold=True, color=COL_A)
tbl = doc.add_table(rows=1, cols=1); c = tbl.cell(0,0); set_cell_bg(c,"F0FFF4")
c.paragraphs[0].clear()
r = c.paragraphs[0].add_run(
    "Je reconnais ne pas avoir paye Fatou en fevrier et mars 2026. J'ai eu des difficultes "
    "financieres dues a un probleme de sante. Je suis en mesure de payer la totalite "
    "des 160 000 FCFA ce mois d'avril, avant le 30 avril 2026. Je m'engage egalement a "
    "regulariser le contrat de travail et a immatriculer Fatou a la CNPS d'ici le 30 mai 2026."
)
r.font.size=Pt(10); r.font.color.rgb=rgb("1A6A2A")
c.paragraphs[0].paragraph_format.left_indent=Cm(0.4)
c.paragraphs[0].paragraph_format.space_before=Pt(5)
c.paragraphs[0].paragraph_format.space_after=Pt(5)
doc.add_paragraph()

h2(doc, "Saisie de l'accord de mediation", color=COL_A)
form_table(doc, [
    ("Resultat de la seance",       "AGREEMENT",                      "Liste => Accord trouve"),
    ("Texte de l'accord",           "Mme KONAN Adjoua s'engage a verser a Mme COULIBALY Fatou la somme de 160 000 FCFA representant les salaires de fevrier et mars 2026, au plus tard le 30 avril 2026. En cas de non-paiement a cette date, la plaignante pourra saisir directement le Tribunal du Travail d'Abidjan.", "Texte long"),
    ("Terme 1 (JSON)",              "Paiement de 160 000 FCFA avant le 30/04/2026",             "Texte"),
    ("Terme 2 (JSON)",              "Etablissement d'un contrat de travail ecrit avant le 30/04/2026","Texte"),
    ("Terme 3 (JSON)",              "Immatriculation COULIBALY Fatou a la CNPS avant le 30/05/2026", "Texte"),
    ("Obligation employeur",        "Paiement 160 000 FCFA + regularisation CNPS + contrat ecrit",   "Texte"),
    ("Date limite execution",       "30/04/2026",                                                    "Date"),
    ("Montant compensation",        "160 000",                                                       "Nombre"),
], color=COL_A)
action_box(doc, "Cliquer 'Enregistrer l'accord' => Cliquer 'Generer PDF pour signature'")
result_box(doc, "PDF de l'accord genere. Les 3 parties signent : COULIBALY Fatou + KONAN Adjoua + Mme DIALLO (signature electronique ou manuscrite). Accord archive dans GED.")

h2(doc, "Cloture de la seance", color=COL_A)
form_table(doc, [
    ("Statut de la seance", "COMPLETED",                      "Liste"),
    ("Resultat final",      "AGREEMENT",                      "Auto-rempli"),
    ("Heure de fin",        "10h45",                          "Heure"),
    ("Notes de cloture",    "Accord signe par les deux parties. PV de mediation archive. Suivi prevu le 02/05/2026 pour verification du paiement.", "Texte"),
], color=COL_A)
action_box(doc, "Cliquer 'Cloturer la seance' => Confirmer")
result_box(doc, "Seance COMPLETED | Plainte PLT-2026-A-000456 => Statut : RESOLU_ACCORD | Notification email+SMS a COULIBALY Fatou : 'Votre litige a ete resolu par accord amiable. Accord reference ACC-2026-000089.'")

# ── ETAPE A5 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "A5", "SUIVI ET CLOTURE DEFINITIVE DU DOSSIER A", COL_A)

h2(doc, "Le 02/05/2026 : Verification du paiement", color=COL_A)
para(doc, "L'inspectrice contacte COULIBALY Fatou pour confirmer que le paiement a ete effectue.")
form_table(doc, [
    ("Type de note",  "SUIVI_ACCORD",                                       "Liste"),
    ("Date",          "02/05/2026",                                         "Date"),
    ("Contenu",       "Appel de COULIBALY Fatou. Confirme avoir reçu 160 000 FCFA le 28/04/2026 via virement mobile. Contrat de travail signe reçu le 25/04/2026. Immatriculation CNPS en cours (rendez-vous CNPS le 08/05/2026). Accord respecte. Dossier peut etre clos definitivement.", "Texte long"),
    ("Accord respecte","OUI",                                               "Oui/Non"),
], color=COL_A)
action_box(doc, "Cliquer 'Enregistrer le suivi' => Cliquer 'Cloturer definitivement la plainte'")
result_box(doc, "Plainte PLT-2026-A-000456 => Statut CLOTURE | Archive GED avec tous les documents | Dossier ferme le 02/05/2026")
alert(doc, "SCENARIO A TERMINE : Litige resolu en 26 jours par accord amiable. Aucune procedure judiciaire necessaire.", "success")

doc.add_page_break()

# =============================================================================
# SCENARIO B
# =============================================================================
banner(doc, "SCENARIO B  --  BAMBA Awa  --  Employe d'entreprise  --  Harcelement moral", bg=COL_B, size=12)

para(doc, (
    "BAMBA Awa travaille comme assistante commerciale chez CITRADE SARL depuis le 15 juin 2023. "
    "Son salaire est de 220 000 FCFA/mois. Depuis octobre 2025, son superieur M. ESSIS Patrice (DG) "
    "lui impose des heures supplementaires non remunerees, lui retire ses dossiers sans justification, "
    "la critique publiquement devant ses collegues et lui impose des objectifs impossibles a atteindre. "
    "Elle a des certificats medicaux pour burn-out en fevrier 2026. Elle depose plainte le 06 avril 2026."
))

# ── ETAPE B1 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "B1", "CONNEXION ET DEPOT DE PLAINTE (Employe d'entreprise)", COL_B)

h2(doc, "Ecran : Connexion", color=COL_B)
form_table(doc, [
    ("Adresse email", "awa.bamba@test.ci", "Texte"),
    ("Mot de passe",  "Test@2026!",        "Mot de passe"),
], color=COL_B)
action_box(doc, "Se connecter => Menu : Mes plaintes => + Deposer une plainte")

h2(doc, "Formulaire de plainte - Section 1 : Identification de l'entreprise", color=COL_B)
form_table(doc, [
    ("Type d'employeur",     "ENTREPRISE",                                      "Liste"),
    ("Rechercher entreprise","CITRADE",                                          "Recherche auto-complete"),
    ("Entreprise selectionnee","CITRADE SARL - CI-ABJ-2022-B-18904",            "Auto-rempli apres selection"),
    ("Responsable mis en cause","M. ESSIS Patrice, Directeur General",          "Texte"),
    ("Adresse entreprise",   "Plateau - Immeuble Woodin Center, 3e etage",      "Auto-rempli"),
], title="Section 1 : Entreprise", color=COL_B)

h2(doc, "Formulaire de plainte - Section 2 : Nature du litige", color=COL_B)
form_table(doc, [
    ("Categorie de plainte",     "HARCELEMENT_MORAL",           "Liste deroulante"),
    ("Date du premier fait",     "01/10/2025",                  "Date"),
    ("Date du dernier fait",     "31/03/2026",                  "Date"),
    ("Priorite estimee",         "URGENT",                      "Liste (harcelement = urgence)"),
    ("Plainte confidentielle",   "OUI - Cocher la case",        "Case a cocher"),
    ("Montant reclame (FCFA)",   "0 (harcelement - reparation morale)", "Nombre"),
], title="Section 2 : Nature du litige", color=COL_B)

h2(doc, "Formulaire de plainte - Section 3 : Description des faits", color=COL_B)
para(doc, "Copier exactement ce texte dans le champ 'Description des faits' :", bold=True, color=COL_B)
tbl = doc.add_table(rows=1, cols=1); c = tbl.cell(0,0); set_cell_bg(c,"F9F0FF")
c.paragraphs[0].clear()
r = c.paragraphs[0].add_run(
    "Je travaille chez CITRADE SARL depuis le 15 juin 2023 comme assistante commerciale. "
    "Depuis octobre 2025, mon superieur M. ESSIS Patrice me soumet a des comportements que je considere "
    "comme du harcelement moral : "
    "(1) Il m'impose regulierement des heures supplementaires non payees (20 a 30h/mois) sans accord ecrit. "
    "(2) Il m'a retire 3 dossiers clients importants sans explication en novembre 2025, devant toute l'equipe. "
    "(3) Il me critique systematiquement lors des reunions hebdomadaires en utilisant des termes humiliants. "
    "(4) Il fixe des objectifs irrealisables et m'informe de l'echec devant les collegues. "
    "Ces agissements ont deteriore gravement ma sante. J'ai ete en arret maladie du 10 au 28 fevrier 2026 "
    "pour syndrome anxieux et burn-out (certificat medical joint). "
    "Deux temoins collegues sont prets a confirmer ces faits. "
    "Je demande l'intervention de l'Inspection du Travail pour faire cesser ces agissements et "
    "obtenir reparation du prejudice subi."
)
r.font.size=Pt(10); r.font.color.rgb=rgb("4A1870")
c.paragraphs[0].paragraph_format.left_indent=Cm(0.4)
c.paragraphs[0].paragraph_format.space_before=Pt(5)
c.paragraphs[0].paragraph_format.space_after=Pt(5)
doc.add_paragraph()

h2(doc, "Formulaire de plainte - Section 4 : Pieces jointes", color=COL_B)
form_table(doc, [
    ("Piece 1 : Certificat medical",     "Certificat burn-out Dr TRAORE 28/02/2026 - signer.pdf",           "PDF"),
    ("Piece 2 : Emails harcelement",     "Capture emails instructions imposant HS non payees",               "JPG/PDF"),
    ("Piece 3 : SMS / messages Teams",   "Captures messages humiliants de M. ESSIS",                        "JPG/PNG"),
    ("Piece 4 : Bulletin de paie",       "Bulletins octobre 2025 a mars 2026 (sans H. supp. payees)",        "PDF"),
    ("Piece 5 : Attestation temoin 1",   "Attestation ecrite et signee de Mme GOLI Marthe (collegue)",      "PDF"),
], title="Section 4 : Pieces jointes", color=COL_B)
action_box(doc, "Cliquer 'Soumettre la plainte' => Confirmer")
result_box(doc, "Numero : PLT-2026-B-000457 | Statut : SUBMITTED | Email envoye a awa.bamba@test.ci | Visible uniquement par inspecteur assigne et Chef inspection (confidentielle)")

# ── ETAPE B2 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "B2", "ASSIGNATION PAR LE CHEF INSPECTION", COL_B)

h2(doc, "Connexion Chef inspection BAMBA Lassina", color=COL_B)
para(doc, "Apres connexion, le Chef inspection voit les 2 plaintes. Il ouvre PLT-2026-B-000457.")

h2(doc, "Formulaire d'assignation - Plainte B", color=COL_B)
form_table(doc, [
    ("Inspecteur assigne",      "DIALLO Aissata",                                     "Liste"),
    ("Priorite",                "URGENT",                                              "Liste"),
    ("Date limite",             "06/05/2026",                                          "Date"),
    ("Classification",          "CONFIDENTIEL - Harcelement moral",                    "Tag"),
    ("Note interne",            "Plainte harcelement moral CONFIDENTIELLE. Auditions separees obligatoires. Ne pas confronter les parties avant le rapport d'enquete. Contacter Mme BAMBA Awa en prive pour l'audition avant de contacter l'entreprise. Voir pieces jointes sensibles.", "Texte long"),
], color=COL_B)
action_box(doc, "Cliquer 'Assigner (Confidentiel)' => Notification chiffree a Mme DIALLO uniquement")
result_box(doc, "Statut : EN_INSTRUCTION | Seule Mme DIALLO peut voir le detail. Le compte CITRADE ne voit rien encore. SMS a BAMBA Awa : 'Dossier PLT-2026-B-000457 pris en charge de facon confidentielle.'")

# ── ETAPE B3 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "B3", "INVESTIGATION : AUDITIONS ET ENQUETE", COL_B)

h2(doc, "Etape 3A : Audition de BAMBA Awa (cote employe)", color=COL_B)
para(doc, "L'inspectrice convoque Mme BAMBA Awa pour une audition confidentielle au bureau DGT le 09/04/2026.")
form_table(doc, [
    ("Type d'evenement",  "AUDITION_EMPLOYE",              "Liste"),
    ("Date",             "09/04/2026 10h00",               "Date-heure"),
    ("Lieu",             "Bureau DGT Plateau - Bureau 204 (prive)", "Texte"),
    ("Convocation",      "Email uniquement (pas de SMS pour eviter decouverte par employeur)", "Note"),
], color=COL_B)
action_box(doc, "Envoyer convocation email a awa.bamba@test.ci")
result_box(doc, "Email envoye. BAMBA Awa repond : 'Confirmee pour le 09/04 a 10h00'")

h2(doc, "Rapport d'audition employe (a saisir apres la rencontre)", color=COL_B)
form_table(doc, [
    ("Date/heure audition","09/04/2026 10h00 - 11h30",   "Date-heure"),
    ("Duree",             "1h30",                          "Texte"),
    ("Resume declaratoire","Mme BAMBA Awa confirme les faits decrits dans la plainte. Elle apporte des preuves supplementaires : email du 15/01/2026 de M. ESSIS imposant 30h supp non payees + capture Teams du 10/03/2026 avec insultes publiques. Elle cite 2 temoins : Mme GOLI Marthe et M. DOSSO Lamine, prets a temoigner.", "Texte long"),
    ("Conclusion partielle","Allegations serieuses et documentees. Enquete cote employeur necessaire.", "Texte"),
], color=COL_B)
action_box(doc, "Enregistrer le rapport d'audition employe")

h2(doc, "Etape 3B : Demande de documents a l'entreprise", color=COL_B)
para(doc, "L'inspectrice adresse une demande de documents a CITRADE SARL (phase administrative avant convocation).")
form_table(doc, [
    ("Destinataire",  "CITRADE SARL - M. ESSIS Patrice - Direction",  "Texte"),
    ("Mode d'envoi",  "Email + Courrier recommande avec AR",           "Liste"),
    ("Documents demandes (1)","Registre du personnel (nominatif complet)","Texte"),
    ("Documents demandes (2)","Bulletins de paie de Mme BAMBA Awa (oct 2025 a mars 2026)","Texte"),
    ("Documents demandes (3)","Contrat de travail de Mme BAMBA Awa",    "Texte"),
    ("Documents demandes (4)","Reglement interieur de l'entreprise",     "Texte"),
    ("Documents demandes (5)","Releves de presence / feuilles de pointage de Mme BAMBA", "Texte"),
    ("Delai de remise",       "72 heures - Avant le 12/04/2026 17h00", "Texte"),
    ("Base legale",           "Art. 94 CT - Pouvoir d'investigation de l'Inspecteur du Travail", "Texte"),
], color=COL_B)
action_box(doc, "Cliquer 'Envoyer la demande de documents' => Email + notification dans le compte CITRADE")
result_box(doc, "Email envoye a essis.citrade@test.ci | Notification dans l'espace CITRADE : 'L'Inspection du Travail vous demande des documents sous 72h (ref. DGT-REQ-20260409-001)'")

# ── ETAPE B4 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "B4", "1ERE CONVOCATION MEDIATION - CITRADE ABSENT", COL_B)

h2(doc, "Generation de la convocation a la mediation", color=COL_B)
para(doc, "CITRADE n'a pas transmis les documents dans les delais (absence de reponse au 12/04). L'inspectrice passe a la convocation formelle de mediation.")
action_box(doc, "Mediations => Nouvelle seance => Remplir le formulaire")
form_table(doc, [
    ("Date de la seance",     "13/04/2026",                                          "Date"),
    ("Heure",                 "09h00",                                               "Heure"),
    ("Type de seance",        "PRESENTIAL",                                          "Liste"),
    ("Lieu",                  "DGT Plateau - Salle de Mediation A - Rez-de-chaussee","Texte"),
    ("Participant 1",         "BAMBA Awa - EMPLOYE - awa.bamba@test.ci",             "Ajouter"),
    ("Participant 2",         "CITRADE SARL / M. ESSIS Patrice - EMPLOYEUR - essis.citrade@test.ci","Ajouter"),
    ("Objet",                 "Tentative de conciliation - Harcelement moral - Plainte PLT-2026-B-000457 - Presence OBLIGATOIRE des deux parties","Texte long"),
    ("Mode de convocation",   "Email recommande + lettre RAR + notification plateforme",  "Cases a cocher"),
], color=COL_B)
action_box(doc, "Cliquer 'Creer la seance et envoyer les convocations' => Confirmer")
result_box(doc, "Convocations envoyees. Statut seance : SCHEDULED. BAMBA Awa confirme sa presence (acknowledged_at enregistre). CITRADE : aucune confirmation reçue.")

alert(doc, "Le 13/04/2026 a 09h00 : BAMBA Awa est presente. CITRADE SARL - M. ESSIS Patrice - ABSENT. Aucun representant, aucun motif communique.", "danger")

h2(doc, "Constat de non-comparution - 1ere absence (13/04/2026)", color=COL_B)
action_box(doc, "Seance MED-2026-000124 => Demarrer la seance => Appel des parties")
form_table(doc, [
    ("BAMBA Awa",              "Cocher 'Presente' => attended = true",  "Case a cocher"),
    ("CITRADE SARL (ESSIS)",   "Cocher 'Absent' => attended = false",   "Case a cocher"),
    ("Non-comparution employeur","Cocher 'Oui' => employer_no_show = true", "Case a cocher"),
    ("Heure du constat",       "09h15",                                  "Heure auto"),
    ("Motif declare",          "Aucun motif communique par l'employeur", "Texte"),
], color=COL_B)
action_box(doc, "Cliquer 'Confirmer la non-comparution' => Cliquer 'Generer PV de 1ere absence'")
result_box(doc, "PV de 1ere absence genere - REF : PV-ABS-2026-000031 | employer_no_show = true | pv_carence_generated = true pour la 1ere occurrence | PDF archieve GED | Notification Chef inspection BAMBA")
action_box(doc, "Cloturer la seance : Statut => CANCELLED | Motif : NON_COMPARUTION_EMPLOYEUR")

# ── ETAPE B5 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "B5", "2EME CONVOCATION - CITRADE TOUJOURS ABSENT => PV DE CARENCE", COL_B)

h2(doc, "Envoi de la 2eme convocation (17/04/2026)", color=COL_B)
para(doc, "Conformement a la procedure, l'inspectrice envoie une 2eme convocation avec lettre recommandee avec avis de reception (RAR).")
action_box(doc, "Mediations => Nouvelle seance => Remplir")
form_table(doc, [
    ("Date de la seance",     "20/04/2026",                  "Date"),
    ("Heure",                 "09h00",                       "Heure"),
    ("Type de seance",        "PRESENTIAL",                  "Liste"),
    ("Lieu",                  "DGT Plateau - Salle A",       "Texte"),
    ("Note importante",       "2EME ET DERNIERE CONVOCATION avant saisine judiciaire. L'absence sans motif valable entrainera l'etablissement d'un PV de carence et la transmission du dossier au Tribunal du Travail d'Abidjan.", "Texte long"),
    ("Mode de convocation",   "Lettre RAR postale + email + notification plateforme", "Texte"),
    ("Participants",          "BAMBA Awa + CITRADE SARL/ESSIS Patrice",              "Ajouter"),
    ("Lien plainte",          "PLT-2026-B-000457",            "Reference"),
], color=COL_B)
action_box(doc, "Creer la seance + Envoyer les convocations + Cocher 'Marquer comme 2eme convocation'")
result_box(doc, "Seance SCHEDULED | postpone_count = 1 | 2e convocation envoyee | Chef inspection et Directeur Regional informes automatiquement")

alert(doc, "Le 20/04/2026 a 09h00 : BAMBA Awa presente. CITRADE SARL ABSENT pour la 2eme fois. Aucun motif. Aucune reponse a la lettre RAR.", "danger")

h2(doc, "Constat de non-comparution - 2eme absence (20/04/2026)", color=COL_B)
form_table(doc, [
    ("BAMBA Awa",             "Presente => attended = true",     "Case a cocher"),
    ("CITRADE SARL (ESSIS)",  "Absent => attended = false",      "Case a cocher"),
    ("Non-comparution",       "employer_no_show = true (x2)",    "Constate"),
    ("Nombre de reports",     "postpone_count = 2",              "Compteur auto"),
], color=COL_B)
action_box(doc, "Cliquer 'Confirmer 2eme non-comparution' => Cliquer 'Generer PV de CARENCE DEFINITIF'")
result_box(doc, "PV de Carence Definitif genere - REF : PV-CAR-2026-000008 | pv_carence_generated = true | PDF signe numeriquement par Mme DIALLO | Archive dans GED | Notification au Chef inspection + Directeur Regional + DG")
action_box(doc, "Cloturer seance : CANCELLED | Raison : NON_COMPARUTION_REPETEE_EMPLOYEUR")

# ── ETAPE B6 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "B6", "SAISINE DU TRIBUNAL DU TRAVAIL D'ABIDJAN", COL_B)

h2(doc, "Le Chef inspection valide la transmission judiciaire", color=COL_B)
para(doc, "Mme DIALLO soumet le dossier au Chef inspection pour validation avant saisine judiciaire.")
action_box(doc, "Workflow => Soumettre pour approbation => Objet : Saisine tribunal PLT-2026-B-000457")
form_table(doc, [
    ("Destinataire validation","BAMBA Lassina - CHEF_INSPECTION",    "Liste"),
    ("Motif de la saisine",   "Double non-comparution de CITRADE SARL aux convocations de mediation des 13 et 20 avril 2026. PV de carence etabli. Harcelement moral documente (certificat medical + temoins + preuves electroniques). Impossibilite de conciliation amiable.", "Texte long"),
    ("Urgence",               "OUI - Harcelement en cours",          "Case a cocher"),
], color=COL_B)
action_box(doc, "Soumettre pour validation au Chef inspection")

h2(doc, "Chef inspection valide et transmet (22/04/2026)", color=COL_B)
action_box(doc, "Chef inspection => Workflow => Approbations => PLT-2026-B-000457 => Valider et transmettre")
result_box(doc, "Dossier approuve | Statut plainte : TRANSMIS_TRIBUNAL | Notification a Mme DIALLO, Directeur Regional et BAMBA Awa")

h2(doc, "Creation de la procedure judiciaire", color=COL_B)
action_box(doc, "Judiciaire => Nouvelle procedure => Remplir le formulaire")
form_table(doc, [
    ("Reference plainte",      "PLT-2026-B-000457",                            "Auto-rempli"),
    ("Type de procedure",      "CONCILIATION_PRUD_HOMALE",                     "Liste"),
    ("Demandeur",              "BAMBA Awa - Assistante commerciale - EMPLOYE",  "Texte"),
    ("Defendeur",              "CITRADE SARL - M. ESSIS Patrice - DG",         "Texte"),
    ("Tribunal competent",     "Tribunal du Travail d'Abidjan - Section Plateau","Liste"),
    ("Motifs de la saisine",   "1) Harcelement moral repete et documente (Art. 4.2 CT CI) 2) Heures supplementaires non payees (Art. 21 CT) 3) Non-comparution employeur a 2 seances de mediation (PV carence REF: PV-CAR-2026-000008)", "Texte long"),
    ("Reparations demandees",  "Cessation immediate du harcelement + Dommages-interets 3 mois salaire (660 000 FCFA) + Rappel H. supp. 18 mois (calculer) + Remise attestation travail", "Texte long"),
    ("Pieces du dossier",      "PV carence PV-CAR-2026-000008 + PV 1ere absence + Rapport audition + Certificat medical + Preuves electroniques + Attestation temoins", "Texte"),
    ("Date de depot prevue",   "22/04/2026",                                   "Date"),
    ("Urgence / Refere",       "NON - Procedure au fond",                      "Liste"),
], color=COL_B)
action_box(doc, "Cliquer 'Creer la procedure et generer la requete'")
result_box(doc, "Procedure judiciaire PROC-2026-000041 creee | Requete PDF generee | Statut : EN_COURS | Notification BAMBA Awa : 'Votre dossier a ete transmis au Tribunal du Travail d'Abidjan.'")

# ── ETAPE B7 ─────────────────────────────────────────────────────────────────
etape_banner(doc, "B7", "AUDIENCE AU TRIBUNAL DU TRAVAIL", COL_B)

h2(doc, "Enregistrement de l'audience (07/05/2026)", color=COL_B)
para(doc, "Le tribunal fixe l'audience au 07 mai 2026. L'inspectrice enregistre la date sur la plateforme.")
action_box(doc, "Judiciaire => PROC-2026-000041 => Nouvelle audience")
form_table(doc, [
    ("Type d'audience",    "AUDIENCE_FOND",                                  "Liste"),
    ("Date",               "07/05/2026",                                     "Date"),
    ("Heure",              "09h00",                                          "Heure"),
    ("Lieu",               "Tribunal du Travail d'Abidjan - Salle 3, 2e etage","Texte"),
    ("Juge president",     "Mme ASSEMIEN Koffi Marie-Therese - President Chambre Sociale", "Texte"),
    ("Statut",             "SCHEDULED",                                      "Liste"),
], color=COL_B)
action_box(doc, "Cliquer 'Enregistrer l'audience' => Notification a BAMBA Awa avec date et heure")

h2(doc, "Apres l'audience : saisie de la decision (07/05/2026 - fin d'apres-midi)", color=COL_B)
para(doc, "Le tribunal a rendu sa decision le jour meme apres delibere.")
form_table(doc, [
    ("Statut audience",        "TENUE",                                      "Liste"),
    ("Resultat plaidoiries",   "Mme BAMBA Awa representee par conseil. CITRADE SARL represente par son directeur M. ESSIS Patrice (comparution forcee suite citation directe). M. ESSIS ne nie pas les faits mais conteste la qualification de harcelement. Le tribunal a entendu les deux temoins (GOLI Marthe et DOSSO Lamine). Decision mise en delibere.", "Texte long"),
    ("Type de decision",       "CONDAMNATION",                              "Liste"),
    ("Date de la decision",    "07/05/2026",                                "Date"),
    ("Dispositif de la decision","1) CITRADE SARL condamne a verser a BAMBA Awa la somme de 660 000 FCFA a titre de dommages-interets pour harcelement moral (Art. 4.2 CT). 2) Rappel heures supplementaires : 245 000 FCFA. 3) Total : 905 000 FCFA - payables sous 30 jours. 4) Avertissement judiciaire a M. ESSIS Patrice. 5) Depot du rapport final a la DGT.", "Texte long"),
    ("Statut de la procedure", "CLOTUREE_CONDAMNATION",                    "Liste"),
    ("Delai execution",        "06/06/2026",                               "Date"),
    ("Montant total condamnation","905 000 FCFA",                          "Nombre"),
], color=COL_B)
action_box(doc, "Cliquer 'Enregistrer la decision' => Cliquer 'Cloturer la procedure'")
result_box(doc, "Procedure PROC-2026-000041 => CLOTUREE | Plainte PLT-2026-B-000457 => RESOLU_JUGEMENT | Notification a BAMBA Awa : 'Decision rendue en votre faveur : 905 000 FCFA. Execution sous 30 jours.' | Archive GED complet")
alert(doc, "SCENARIO B TERMINE : Litige resolu en 31 jours par decision judiciaire. Harcelement reconnu. Employeur condamne a 905 000 FCFA.", "success")

doc.add_page_break()

# =============================================================================
# TABLEAU COMPARATIF
# =============================================================================
banner(doc, "TABLEAU COMPARATIF DES DEUX PARCOURS", bg=BLEU)

data_table(doc,
    ["Etape", "Scenario A - Employe de maison", "Scenario B - Employe entreprise"],
    [
        ["Depot plainte",        "06/04/2026 - PLT-2026-A-000456",            "06/04/2026 - PLT-2026-B-000457"],
        ["Type plainte",         "NON_PAIEMENT_SALAIRE",                      "HARCELEMENT_MORAL (Confidentielle)"],
        ["Assignation",          "CHEF => Mme DIALLO (priorite HIGH)",         "CHEF => Mme DIALLO (priorite URGENT)"],
        ["Prise en charge",      "06/04/2026 10h30",                          "06/04/2026 10h35"],
        ["Contact employeur",    "Appel tel. - KONAN accepte mediation",       "Demande documents (ignoree) + convocations"],
        ["1re seance",           "13/04/2026 - KONAN PRESENTE",               "13/04/2026 - ESSIS ABSENT"],
        ["Resultat 1re seance",  "Accord trouve (AGREEMENT)",                  "PV 1ere absence - REF PV-ABS-2026-000031"],
        ["2e seance",            "N/A - 1 seule seance suffisante",           "20/04/2026 - ESSIS ABSENT x2"],
        ["Resultat 2e seance",   "N/A",                                        "PV de carence - REF PV-CAR-2026-000008"],
        ["Accord mediation",     "ACC-2026-000089 signe 13/04",               "Aucun accord - Refus employeur"],
        ["Procedure judiciaire", "Non necessaire",                            "PROC-2026-000041 - Tribunal Abidjan"],
        ["Audience tribunal",    "N/A",                                        "07/05/2026 - Tribunal du Travail Abidjan"],
        ["Decision finale",      "Accord : 160 000 FCFA verse le 28/04",      "Condamnation : 905 000 FCFA sous 30j"],
        ["Duree totale",         "26 jours (06/04 => 02/05/2026)",            "31 jours (06/04 => 07/05/2026)"],
        ["Statut final",         "CLOTURE - RESOLU_ACCORD",                   "CLOTURE - RESOLU_JUGEMENT"],
    ],
    hbg=BLEU,
    wids=[4.5, 6.5, 6.5]
)

# =============================================================================
# RECAP DES CHAMPS CLES
# =============================================================================
banner(doc, "RECAP DES DONNEES CLES SAISIES SUR LA PLATEFORME", bg=ORANGE)

h2(doc, "Scenario A : Champs remplis", color=COL_A)
data_table(doc,
    ["Module","Champ","Valeur finale"],
    [
        ["Plainte",    "complaint_number",        "PLT-2026-A-000456"],
        ["Plainte",    "category",                "NON_PAIEMENT_SALAIRE"],
        ["Plainte",    "priority",                "HIGH"],
        ["Plainte",    "amount_claimed",          "160 000 FCFA"],
        ["Plainte",    "status (final)",          "RESOLU_ACCORD"],
        ["Mediation",  "session_date",            "2026-04-13 09:07"],
        ["Mediation",  "attended (COULIBALY)",    "True"],
        ["Mediation",  "attended (KONAN)",        "True"],
        ["Mediation",  "employer_no_show",        "False"],
        ["Mediation",  "outcome",                 "AGREEMENT"],
        ["Mediation",  "compensation_amount",     "160 000 FCFA"],
        ["Accord",     "execution_deadline",      "2026-04-30"],
        ["Accord",     "status",                  "EXECUTED (paiement confirme 28/04)"],
    ], hbg=COL_A
)

h2(doc, "Scenario B : Champs remplis", color=COL_B)
data_table(doc,
    ["Module","Champ","Valeur finale"],
    [
        ["Plainte",      "complaint_number",       "PLT-2026-B-000457"],
        ["Plainte",      "category",               "HARCELEMENT_MORAL"],
        ["Plainte",      "priority",               "URGENT"],
        ["Plainte",      "is_confidential",        "True"],
        ["Plainte",      "status (final)",         "RESOLU_JUGEMENT"],
        ["Mediation 1",  "session_date",           "2026-04-13 09:00"],
        ["Mediation 1",  "employer_no_show",       "True"],
        ["Mediation 1",  "pv_carence_generated",   "True (1ere absence)"],
        ["Mediation 2",  "session_date",           "2026-04-20 09:00"],
        ["Mediation 2",  "employer_no_show",       "True"],
        ["Mediation 2",  "postpone_count",         "2"],
        ["Mediation 2",  "pv_carence_generated",   "True (definitif)"],
        ["Judiciaire",   "procedure_type",         "CONCILIATION_PRUD_HOMALE"],
        ["Judiciaire",   "tribunal",               "Tribunal du Travail Abidjan"],
        ["Judiciaire",   "decision_type",          "CONDAMNATION"],
        ["Judiciaire",   "montant_condamnation",   "905 000 FCFA"],
    ], hbg=COL_B
)

# Pied de page
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(20)
r = p.add_run("eInspection CI - Cas d'usage complet | DGT Cote d'Ivoire 2026 | Code du Travail CI Loi 2015-532")
r.font.size=Pt(8.5); r.font.color.rgb=rgb("888888"); r.italic=True

output = "CasUsage_DeuxEmployes_eInspection.docx"
doc.save(output)
print("Document genere : " + output)

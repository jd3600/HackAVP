# backend/pdf_generator.py
import io
import os
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape

MAPPING_FICHE_RENSEIGNEMENTS = {
    "poste_employeur_public": {"x": 129.1, "y": 713.7, "type": "texte"},
    "poste_direction": {"x": 404.2, "y": 714.7, "type": "texte"},
    "poste_num_reference": {"x": 131.1, "y": 694.4, "type": "texte"},
    "poste_date_cloture": {"x": 403.2, "y": 694.4, "type": "texte"},
    "poste_intitule": {"x": 136.1, "y": 675.1, "type": "texte"},
    "case_civilite_m": {"x": 134.1, "y": 623.6, "type": "case"},
    "case_civilite_mme": {"x": 175.1, "y": 623.6, "type": "case"},
    "nom_prenom": {"x": 261.1, "y": 624.7, "type": "texte"},
    "date_naissance": {"x": 123.1, "y": 603.3, "type": "texte"},
    "lieu_naissance": {"x": 357.2, "y": 603.3, "type": "texte"},
    "email": {"x": 127.1, "y": 586.1, "type": "texte"},
    "telephone": {"x": 129.1, "y": 564.7, "type": "texte"},
    "case_nationalite_francaise_oui": {"x": 469.2, "y": 562.6, "type": "case"},
    "case_nationalite_francaise_non": {"x": 511.2, "y": 562.6, "type": "case"},
    "case_parent_fonctionnaire_nc": {"x": 31.0, "y": 526.5, "type": "case"},
    "case_fonctionnaire_nc": {"x": 60.0, "y": 509.0, "type": "case"},
    "case_fct_nc_titulaire": {"x": 241.1, "y": 509.0, "type": "case"},
    "case_fct_nc_stagiaire": {"x": 291.1, "y": 510.1, "type": "case"},
    "case_fonctionnaire_communal": {"x": 60.0, "y": 492.9, "type": "case"},
    "case_fct_communal_titulaire": {"x": 190.1, "y": 493.8, "type": "case"},
    "case_fct_communal_stagiaire": {"x": 239.1, "y": 492.9, "type": "case"},
    "case_laureat_concours": {"x": 61.0, "y": 474.7, "type": "case"},
    "laureat_annee": {"x": 388.2, "y": 475.5, "type": "texte"},
    "laureat_corps": {"x": 486.2, "y": 473.4, "type": "texte"},
    "case_filiere_admin": {"x": 137.1, "y": 458.6, "type": "case"},
    "case_filiere_technique": {"x": 265.1, "y": 458.6, "type": "case"},
    "case_filiere_opt": {"x": 331.1, "y": 457.6, "type": "case"},
    "case_filiere_sante_social": {"x": 380.2, "y": 457.6, "type": "case"},
    "case_filiere_enseignement": {"x": 444.2, "y": 456.5, "type": "case"},
    "case_filiere_culture_sport": {"x": 138.1, "y": 441.5, "type": "case"},
    "case_filiere_incendie": {"x": 381.2, "y": 441.5, "type": "case"},
    "case_filiere_securite": {"x": 444.2, "y": 440.4, "type": "case"},
    "case_categorie_a": {"x": 138.1, "y": 426.5, "type": "case"},
    "case_categorie_b": {"x": 168.1, "y": 424.3, "type": "case"},
    "case_categorie_c": {"x": 196.1, "y": 424.3, "type": "case"},
    "case_situation_activite": {"x": 139.1, "y": 405.1, "type": "case"},
    "case_situation_detachement": {"x": 333.1, "y": 404.0, "type": "case"},
    "date_fin_detachement": {"x": 461.2, "y": 409.8, "type": "texte"},
    "case_situation_disponibilite": {"x": 139.1, "y": 383.6, "type": "case"},
    "date_fin_disponibilite": {"x": 252.1, "y": 384.7, "type": "texte"},
    "case_situation_autre": {"x": 333.2, "y": 384.7, "type": "case"},
    "employeur_public_actuel": {"x": 247.1, "y": 362.2, "type": "texte"},
    "case_parent_non_fonctionnaire": {"x": 31.0, "y": 331.1, "type": "case"},
    "case_agent_fct_metropolitaine": {"x": 60.0, "y": 315.0, "type": "case"},
    "case_metropole_etat": {"x": 342.2, "y": 316.1, "type": "case"},
    "case_metropole_territoriale": {"x": 380.2, "y": 316.1, "type": "case"},
    "case_metropole_hopital": {"x": 446.2, "y": 315.0, "type": "case"},
    "metropole_categorie": {"x": 530.2, "y": 317.3, "type": "texte"},
    "case_agent_contractuel_nc": {"x": 60.0, "y": 299.0, "type": "case"},
    "agent_contractuel_employeur": {"x": 376.2, "y": 298.8, "type": "texte"},
    "case_prive_emploi": {"x": 60.0, "y": 282.9, "type": "case"},
    "case_contractuel_autre": {"x": 60.0, "y": 266.8, "type": "case"},
    "contractuel_autre_precision": {"x": 147.1, "y": 269.0, "type": "texte"},
    "case_citoyen_caledonien": {"x": 33.0, "y": 232.3, "type": "case"},
    "case_resident": {"x": 34.0, "y": 216.5, "type": "case"},
    "date_residence": {"x": 247.1, "y": 215.9, "type": "texte"},
    "annees_residence": {"x": 384.2, "y": 218.1, "type": "texte"},
    "case_non_resident": {"x": 33.0, "y": 200.5, "type": "case"},
    "diplomes": {"x": 215.1, "y": 179.0, "type": "texte"},
    "case_handicap_oui": {"x": 479.2, "y": 139.3, "type": "case"},
    "case_handicap_non": {"x": 515.2, "y": 138.2, "type": "case"},
}

MAPPING_ATTESTATION_NON_RUPTURE = {
    "nom_prenom": {"x": 204.6, "y": 636.7, "type": "texte"},
    "lieu_signature": {"x": 234.6, "y": 516.8, "type": "texte"},
    "date_signature": {"x": 236.6, "y": 469.8, "type": "texte"},
    "signature": {"x": 221.6, "y": 400.5, "type": "texte"},
}

def fusionner_pdf(pdf_modele: str, pdf_sortie: str, donnees: dict, mapping: dict):
    if not os.path.exists(pdf_modele):
        raise FileNotFoundError(f"Modèle non trouvé : {pdf_modele}")

    tampon = io.BytesIO()
    c = canvas.Canvas(tampon, pagesize=A4)
    c.setFillColorRGB(0.05, 0.1, 0.25)

    for cle, valeur in donnees.items():
        if cle not in mapping or valeur is None:
            continue
        champ = mapping[cle]
        x, y = champ["x"], champ["y"]

        if champ["type"] == "case":
            if valeur is True or str(valeur).strip().upper() in ["X", "OUI", "1", "TRUE"]:
                c.setFont("Helvetica-Bold", 10.0)
                c.drawString(x, y, "X")
        else:
            c.setFont("Helvetica", 9.0)
            c.drawString(x, y, str(valeur))

    c.save()
    tampon.seek(0)

    calque = PdfReader(tampon).pages[0]
    modele = PdfReader(pdf_modele)
    writer = PdfWriter()

    page = modele.pages[0]
    page.merge_page(calque)
    writer.add_page(page)

    os.makedirs(os.path.dirname(pdf_sortie), exist_ok=True)
    with open(pdf_sortie, "wb") as f_out:
        writer.write(f_out)


def generer_pdf_dossier_candidat(assets_result: dict) -> bytes:
    """Génère un dossier PDF avec les textes IA et les formulaires officiels présents."""
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="DossierTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=23,
        textColor="#153c3c",
        alignment=1,
        spaceAfter=18,
    ))
    styles.add(ParagraphStyle(
        name="DossierSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor="#16766e",
        spaceBefore=10,
        spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name="DossierBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        spaceAfter=8,
    ))

    sections = [
        ("cv_oriente", "CV orienté"),
        ("lettre_motivation", "Lettre de motivation"),
        ("bilan_ecart", "Bilan des compétences et écarts"),
        ("fiche_entretien", "Préparation à l’entretien"),
        ("raw_text", "Contenu généré"),
    ]
    story = [Paragraph("Dossier de candidature OPT-NC", styles["DossierTitle"])]
    has_content = False
    for key, title in sections:
        content = assets_result.get(key)
        if not content:
            continue
        has_content = True
        text = escape(str(content)).replace("\n", "<br/>")
        story.extend([
            Paragraph(escape(title), styles["DossierSection"]),
            Paragraph(text, styles["DossierBody"]),
        ])

    if not has_content:
        story.append(Paragraph("Aucun contenu textuel n’a été généré.", styles["DossierBody"]))

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Dossier de candidature OPT-NC",
    )
    document.build(story)

    writer = PdfWriter()
    generated_pdf = PdfReader(buffer)
    for page in generated_pdf.pages:
        writer.add_page(page)

    for key in ("fiche_renseignements_pdf", "attestation_non_rupture_pdf"):
        pdf_path = assets_result.get(key)
        if not isinstance(pdf_path, str) or not os.path.isfile(pdf_path):
            continue
        for page in PdfReader(pdf_path).pages:
            writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()

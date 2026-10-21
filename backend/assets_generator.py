# -*- coding: utf-8 -*-
"""
assets_generator.py
Générateur d'assets de candidature pour Copilote RH (OPT-NC).
Assemble la génération de contenu IA (Gemini 2.5) et la création des formulaires PDF officiels (ReportLab).
"""

import os
import json
from datetime import datetime
from google import genai
from pdf_generator import (
    fusionner_pdf,
    MAPPING_FICHE_RENSEIGNEMENTS,
    MAPPING_ATTESTATION_NON_RUPTURE,
)

try:
    ai_client = genai.Client()
except Exception as e:
    ai_client = None
    print(f"⚠️ Avertissement Client IA (Assets) : {e}")

# Chemins vers les modèles PDF officiels de la DRH
TEMPLATE_FICHE = "data/templates/recrutement_-_fiche_de_renseignements_candidature_vf_0.pdf"
TEMPLATE_ATTESTATION = "data/templates/attestation_sur_lhonneur_de_non_benefice_de_la_rupture_conventionnelle.pdf"


def construire_donnees_fiche(
    id_avp_cible: str,
    choix_utilisateur: dict,
    donnees_candidat_raw: dict,
) -> dict:
    administratif = choix_utilisateur.get("situation_administrative") or {}
    statut_principal = administratif.get("statut_principal", "")
    sous_statut = administratif.get("sous_statut", "")
    type_non_fonctionnaire = administratif.get("type_non_fonctionnaire", "")
    filiere = administratif.get("filiere", "")
    categorie = administratif.get("categorie", "")
    situation_actuelle = administratif.get("situation_actuelle", "")
    statut_residence = administratif.get("statut_residence", "")
    statut_pro_legacy = choix_utilisateur.get("statut_pro", "prive")
    est_fonctionnaire = statut_principal == "fct_nc_communes" or (
        not statut_principal and statut_pro_legacy == "fct_nc"
    )
    est_non_fonctionnaire = statut_principal == "agent_non_fct" or (
        not statut_principal and statut_pro_legacy != "fct_nc"
    )
    citoyen = (
        statut_residence == "citoyen"
        if statut_residence
        else choix_utilisateur.get("citoyen_caledonien", True)
    )
    resident = (
        statut_residence == "resident"
        if statut_residence
        else not choix_utilisateur.get("citoyen_caledonien", True)
    )
    date_fin = administratif.get("date_fin_situation", "")

    return {
        "poste_employeur_public": "OPT-NC",
        "poste_direction": choix_utilisateur.get("poste_direction", "Direction Générale"),
        "poste_num_reference": str(id_avp_cible),
        "poste_date_cloture": choix_utilisateur.get("poste_date_cloture", ""),
        "poste_intitule": choix_utilisateur.get("poste_intitule", str(id_avp_cible)),
        "nom_prenom": donnees_candidat_raw.get("nom_prenom", "Candidat_NC"),
        "date_naissance": donnees_candidat_raw.get("date_naissance", ""),
        "lieu_naissance": donnees_candidat_raw.get("lieu_naissance", ""),
        "email": donnees_candidat_raw.get("email", ""),
        "telephone": donnees_candidat_raw.get("telephone", ""),
        "date_residence": donnees_candidat_raw.get("date_residence") or administratif.get("date_residence", ""),
        "annees_residence": donnees_candidat_raw.get("annees_residence") or administratif.get("annees_residence", ""),
        "diplomes": donnees_candidat_raw.get("diplomes", ""),
        "case_civilite_m": choix_utilisateur.get("civilite") == "M",
        "case_civilite_mme": choix_utilisateur.get("civilite") == "MME",
        "case_nationalite_francaise_oui": choix_utilisateur.get("nationalite_francaise", True),
        "case_nationalite_francaise_non": not choix_utilisateur.get("nationalite_francaise", True),
        "case_parent_fonctionnaire_nc": est_fonctionnaire,
        "case_fonctionnaire_nc": sous_statut.startswith("fct_nc_"),
        "case_fct_nc_titulaire": sous_statut == "fct_nc_titulaire",
        "case_fct_nc_stagiaire": sous_statut == "fct_nc_stagiaire",
        "case_fonctionnaire_communal": sous_statut.startswith("fct_communal_"),
        "case_fct_communal_titulaire": sous_statut == "fct_communal_titulaire",
        "case_fct_communal_stagiaire": sous_statut == "fct_communal_stagiaire",
        "case_laureat_concours": sous_statut == "laureat_concours",
        "laureat_annee": administratif.get("annee_concours", ""),
        "laureat_corps": administratif.get("corps_concours", ""),
        "case_filiere_admin": filiere == "administration",
        "case_filiere_technique": filiere == "technique",
        "case_filiere_opt": filiere == "opt",
        "case_filiere_sante_social": filiere == "sante_social",
        "case_filiere_enseignement": filiere == "enseignement",
        "case_filiere_culture_sport": filiere == "culture_sport",
        "case_filiere_incendie": filiere == "incendie",
        "case_filiere_securite": filiere == "securite",
        "case_categorie_a": categorie.upper() == "A",
        "case_categorie_b": categorie.upper() == "B",
        "case_categorie_c": categorie.upper() == "C",
        "case_situation_activite": situation_actuelle == "activite",
        "case_situation_detachement": situation_actuelle == "detachement",
        "date_fin_detachement": date_fin if situation_actuelle == "detachement" else "",
        "case_situation_disponibilite": situation_actuelle == "disponibilite",
        "date_fin_disponibilite": date_fin if situation_actuelle == "disponibilite" else "",
        "case_situation_autre": situation_actuelle == "autre",
        "employeur_public_actuel": administratif.get("employeur_public_actuel", ""),
        "case_parent_non_fonctionnaire": est_non_fonctionnaire,
        "case_agent_fct_metropolitaine": type_non_fonctionnaire == "fct_metropole",
        "case_metropole_etat": type_non_fonctionnaire == "fct_metropole" and administratif.get("branche_metropole") == "etat",
        "case_metropole_territoriale": type_non_fonctionnaire == "fct_metropole" and administratif.get("branche_metropole") == "territoriale",
        "case_metropole_hopital": type_non_fonctionnaire == "fct_metropole" and administratif.get("branche_metropole") == "hopital",
        "metropole_categorie": administratif.get("categorie_metropole", ""),
        "case_agent_contractuel_nc": type_non_fonctionnaire == "contractuel_nc",
        "agent_contractuel_employeur": administratif.get("employeur", "") if type_non_fonctionnaire == "contractuel_nc" else "",
        "case_prive_emploi": type_non_fonctionnaire == "prive_recherche" or (not statut_principal and statut_pro_legacy == "prive"),
        "case_contractuel_autre": type_non_fonctionnaire == "autre",
        "contractuel_autre_precision": administratif.get("employeur", "") if type_non_fonctionnaire == "autre" else "",
        "case_citoyen_caledonien": citoyen,
        "case_resident": resident,
        "case_non_resident": statut_residence == "non_resident",
        "case_handicap_oui": choix_utilisateur.get("handicap", False),
        "case_handicap_non": not choix_utilisateur.get("handicap", False),
    }


def generer_les_quatre_assets(
    profil_structurer: str,
    id_avp_cible: str,
    choix_utilisateur: dict = None,
    donnees_candidat_raw: dict = None,
):
    """
    FONCTION ③ : Génère automatiquement les 4 pièces clés textuelles (CV, Lettre, Bilan, Entretien)
    via Gemini, ET pré-remplit les 2 formulaires PDF officiels (Fiche de renseignements + Attestation).
    """
    if not ai_client:
        raise RuntimeError("Client IA non initialisé.")

    choix_utilisateur = choix_utilisateur or {}
    donnees_candidat_raw = donnees_candidat_raw or {}

    # -----------------------------------------------------------------
    # 1. Génération IA des contenus textuels (Gemini 2.5 Flash)
    # -----------------------------------------------------------------
    prompt = f"""
    Tu es le Copilote RH expert de l'OPT-NC (Nouvelle-Calédonie).
    
    POSTE CIBLÉ (AVP) : {id_avp_cible}
    PROFIL DU CANDIDAT : {profil_structurer}
    
    MISSION :
    Génère de manière détaillée et professionnelle les 4 assets de candidature obligatoires. 
    Le ton doit être formel, respectueux des standards de la fonction publique calédonienne et percutant.
    
    Réponds STRICTEMENT sous forme de JSON structuré avec ces 4 clés exactes :
    1. "cv_oriente": "(Texte formaté du CV optimisé pour mettre en avant les compétences requises par l'AVP)"
    2. "lettre_motivation": "(Texte complet de la lettre de motivation adressée au Directeur des Ressources Humaines de l'OPT-NC)"
    3. "bilan_ecart": "(Synthèse des forces du candidat et des points d'attention / marges de progression pour le poste)"
    4. "fiche_entretien": "(Guide de préparation avec 3 à 4 questions types posées par le jury de l'OPT et des conseils de posture)"
    """

    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )

    # Parsing de la réponse JSON de Gemini
    try:
        resultat_assets = json.loads(response.text)
    except Exception:
        resultat_assets = {"raw_text": response.text}

    # -----------------------------------------------------------------
    # 2. Préparation des données pour la Fiche de Renseignements PDF
    # -----------------------------------------------------------------
    nom_candidat = donnees_candidat_raw.get("nom_prenom", "Candidat_NC")
    nom_clean = nom_candidat.replace(" ", "_")

    donnees_fiche = construire_donnees_fiche(
        id_avp_cible,
        choix_utilisateur,
        donnees_candidat_raw,
    )
    nom_candidat = donnees_fiche["nom_prenom"]
    nom_clean = nom_candidat.replace(" ", "_")

    # -----------------------------------------------------------------
    # 3. Préparation des données pour l'Attestation de Non-Rupture
    # -----------------------------------------------------------------
    donnees_attestation = {
        "nom_prenom": nom_candidat,
        "lieu_signature": choix_utilisateur.get("lieu_signature", "Nouméa"),
        "date_signature": datetime.now().strftime("%d/%m/%Y"),
        "signature": f"Signé numériquement par {nom_candidat}",
    }

    # -----------------------------------------------------------------
    # 4. Fusion et Génération des deux fichiers PDF
    # -----------------------------------------------------------------
    pdf_fiche_out = f"outputs/Fiche_Renseignements_{nom_clean}.pdf"
    pdf_attestation_out = f"outputs/Attestation_Non_Rupture_{nom_clean}.pdf"

    # Injections si les modèles sont présents
    if os.path.exists(TEMPLATE_FICHE):
        fusionner_pdf(TEMPLATE_FICHE, pdf_fiche_out, donnees_fiche, MAPPING_FICHE_RENSEIGNEMENTS)
        resultat_assets["fiche_renseignements_pdf"] = pdf_fiche_out
    else:
        print(f"⚠️ Modèle non trouvé : {TEMPLATE_FICHE}")

    if os.path.exists(TEMPLATE_ATTESTATION):
        fusionner_pdf(TEMPLATE_ATTESTATION, pdf_attestation_out, donnees_attestation, MAPPING_ATTESTATION_NON_RUPTURE)
        resultat_assets["attestation_non_rupture_pdf"] = pdf_attestation_out
    else:
        print(f"⚠️ Modèle non trouvé : {TEMPLATE_ATTESTATION}")

    return resultat_assets
# matching_engine.py
import os
import json
from google import genai
from opt_apigee_client import lister_metiers_apigee, rechercher_avps_apigee

try:
    ai_client = genai.Client()
except Exception as e:
    ai_client = None
    print(f"⚠️ Avertissement Client IA : {e}")

def analyser_et_structurer_profil(description_brute: str):
    """
    FONCTION ① : Ingestion et structuration du profil candidat.
    """
    if not ai_client:
        raise RuntimeError("Client IA non initialisé.")

    prompt = f"""
    Tu es le Copilote RH expert de l'OPT-NC.
    Analyse ce profil brut / CV :
    "{description_brute}"
    
    Convertis-le en un profil structuré au format JSON strict :
    {{
      "nom_candidat": "Candidat",
      "competences_techniques": ["compétence 1", "compétence 2"],
      "competences_comportementales": ["soft skill 1"],
      "experiences_cles": "Synthèse des expériences",
      "domaine_principal": "Domaine principal (ex: Télécoms, IT/DSI, Banque, Guichet, RH, Logistique, Admin)"
    }}
    """
    response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={'response_mime_type': 'application/json'}
    )
    return response.text

def executer_matching_explicable(
    profil_structurer: str | dict,
    id_avp_cible: str = None,
    source_matching: str = "avps",
):
    """Compare le profil à un seul référentiel Apigee selon la source choisie."""
    if not ai_client:
        raise RuntimeError("Client IA non initialisé.")
    if source_matching not in {"avps", "metiers"}:
        raise ValueError("source_matching doit être 'avps' ou 'metiers'.")

    profil_json = (
        json.dumps(profil_structurer, ensure_ascii=False)
        if isinstance(profil_structurer, (dict, list))
        else str(profil_structurer)
    )
    if source_matching == "metiers":
        referentiel = lister_metiers_apigee()
        cle_referentiel = "metiers_disponibles"
        nom_source = "API Métiers OPT-NC"
        champ_code = "code_metier"
    else:
        referentiel = rechercher_avps_apigee(prompt=profil_json, top_k=10)
        cle_referentiel = "avps_recherchees"
        nom_source = "API des AVP OPT-NC"
        champ_code = "code_avp"

    if isinstance(referentiel, dict) and referentiel.get("error"):
        raise RuntimeError(f"Erreur {nom_source} : {referentiel.get('detail', referentiel['error'])}")

    prompt = f"""
    Tu es le Moteur de Matching RH de l'OPT-NC.

    SOURCE DE RÉFÉRENCE : {nom_source}
    DONNÉES RETOURNÉES PAR CETTE SOURCE :
    {json.dumps({cle_referentiel: referentiel}, default=str, ensure_ascii=False)[:10000]}

    PROFIL STRUCTURÉ DU CANDIDAT :
    {profil_json}
    {f'OFFRE À PRIVILÉGIER SI ELLE EST PRÉSENTE : {id_avp_cible}' if id_avp_cible else ''}

    MISSION :
    Utilise uniquement les données fournies par {nom_source}. Identifie jusqu'à 3 résultats pertinents pour le profil. N'invente aucun intitulé ni code; si les données sont insuffisantes, retourne une liste vide. Le score est une estimation d'aide à la décision, pas une mesure objective.

    Renvoie un JSON strict respectant cette structure exacte :
    {{
      "postes_propices": [
        {{
          "intitule": "Intitulé exact retourné par la source",
          "{champ_code}": "Code exact retourné par la source",
                    "date_cloture": "Date exacte de clôture fournie par la source, ou chaîne vide si absente",
          "score_matching": "XX%",
          "fiche_explicable": {{
            "pourquoi_ce_rapprochement": "Explication ancrée dans le profil et les données de la source",
            "points_forts": "Atouts majeurs du candidat pour ce poste",
            "ecarts_a_combler": "Compétences ou prérequis à acquérir",
            "conseil_bienveillant": "Piste d'amélioration concrète"
          }}
        }}
      ]
    }}
    """

    response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={'response_mime_type': 'application/json'}
    )
    return response.text
import os
import requests

# URLs de base officielles issues de la documentation Apigee de l'OPT-NC
METIERS_API_URL = "https://api.opt.nc/metiers-opt"
AVP_API_URL = "https://api.opt.nc/avps"

def get_headers():
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("OPT_API_KEY")
    if api_key:
        headers["x-apikey"] = api_key
    return headers

def lister_metiers_apigee(famille: str = None, actif: bool = None, statut: str = None):
    """Interroge l'API /metiers avec filtres optionnels."""
    try:
        params = {}
        if famille: params["famille"] = famille
        if actif is not None: params["actif"] = str(actif).lower()
        if statut: params["statut"] = statut

        response = requests.get(f"{METIERS_API_URL}/metiers", headers=get_headers(), params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"error": f"Erreur {response.status_code}", "detail": response.text}
    except Exception as e:
        return {"error": str(e)}

def detail_metier_apigee(code_metier: str):
    """Récupère le détail complet d'un métier avec ses compétences."""
    try:
        response = requests.get(f"{METIERS_API_URL}/metiers/{code_metier}", headers=get_headers(), timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"error": f"Erreur {response.status_code}", "detail": response.text}
    except Exception as e:
        return {"error": str(e)}

def rechercher_avps_apigee(prompt: str = None, filters: dict = None, top_k: int = 5):
    """Effectue une recherche sémantique ou structurée sur les AVP via POST /search."""
    try:
        payload = {"options": {"top_k": top_k}}
        if prompt:
            payload["prompt"] = prompt
        if filters:
            payload["filters"] = filters

        response = requests.post(f"{AVP_API_URL}/search", headers=get_headers(), json=payload, timeout=8)
        if response.status_code == 200:
            return response.json()
        return {"error": f"Erreur {response.status_code}", "detail": response.text}
    except Exception as e:
        return {"error": str(e)}

# --- ALIAS DE COMPATIBILITÉ ---
def get_avps_from_apigee():
    """Alias pour compatibilité avec l'ancienne route de test."""
    return rechercher_avps_apigee(top_k=5)

def get_metiers_from_apigee():
    """Alias pour compatibilité avec l'ancienne route de test."""
    return lister_metiers_apigee()

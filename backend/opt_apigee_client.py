import os

import requests

METIERS_API_URL = "https://api.opt.nc/metiers-opt"
AVP_API_URL = "https://api.opt.nc/avps"


def _headers():
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("OPT_API_KEY")
    if api_key:
        headers["x-apikey"] = api_key
    return headers


def _response_json(response):
    if response.ok:
        return response.json()
    return {"error": f"Erreur {response.status_code}", "detail": response.text}


def lister_metiers_apigee(famille=None, actif=None, statut=None):
    params = {}
    if famille:
        params["famille"] = famille
    if actif is not None:
        params["actif"] = str(actif).lower()
    if statut:
        params["statut"] = statut

    try:
        response = requests.get(
            f"{METIERS_API_URL}/metiers",
            headers=_headers(),
            params=params,
            timeout=8,
        )
        return _response_json(response)
    except requests.RequestException as exc:
        return {"error": str(exc)}


def detail_metier_apigee(code_metier):
    try:
        response = requests.get(
            f"{METIERS_API_URL}/metiers/{code_metier}",
            headers=_headers(),
            timeout=8,
        )
        return _response_json(response)
    except requests.RequestException as exc:
        return {"error": str(exc)}


def rechercher_avps_apigee(prompt=None, filters=None, top_k=5):
    payload = {"options": {"top_k": top_k}}
    if prompt:
        payload["prompt"] = prompt
    if filters:
        payload["filters"] = filters

    try:
        response = requests.post(
            f"{AVP_API_URL}/search",
            headers=_headers(),
            json=payload,
            timeout=10,
        )
        return _response_json(response)
    except requests.RequestException as exc:
        return {"error": str(exc)}


def get_avps_from_apigee():
    return rechercher_avps_apigee(top_k=5)


def get_metiers_from_apigee():
    return lister_metiers_apigee()

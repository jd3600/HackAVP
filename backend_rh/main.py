import os
import json
import mimetypes
import traceback
from typing import Optional, List
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, Security, Query, UploadFile, File, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import firestore, storage
from google.api_core.exceptions import NotFound
import firebase_admin
from firebase_admin import credentials, auth

app = FastAPI(
    title="Copilote RH - Espace Recruteur OPT-NC",
    version="3.2.2",
    description="Backend sécurisé par Firebase Auth & Vertex AI pour la gestion des candidatures OPT-NC."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ID = os.getenv("GCP_PROJECT")
DATABASE_ID = os.getenv("FIRESTORE_DATABASE")
BUCKET_CANDIDATS = os.getenv("GCS_BUCKET_CANDIDATS")
BUCKET_WORKSPACE = os.getenv("GCS_BUCKET_WORKSPACE")

# Global clients
db = None
storage_client = None
vertex_client = None

try:
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)
    storage_client = storage.Client(project=PROJECT_ID)
except Exception as e:
    print(f"⚠️ Erreur initialisation GCP/Firebase: {e}")

try:
    from google import genai
    vertex_client = genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")
    print("✅ Client Vertex AI (google-genai) initialisé avec succès sur us-central1.")
except Exception as e:
    print(f"⚠️ Erreur initialisation Vertex AI (google-genai): {e}")

security = HTTPBearer()

def verifier_utilisateur_rh(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=401, 
            detail=f"Échec de l'authentification Firebase : {str(e)}"
        )

class DemandeAccesModel(BaseModel):
    id_avp: str

@app.get("/")
def health_check():
    return {
        "service": "copilote-rh-backend",
        "status": "online",
        "organisation": "OPT-NC • DRH",
        "buckets": {
            "candidats": BUCKET_CANDIDATS,
            "workspace": BUCKET_WORKSPACE
        }
    }

# --- 1. CATALOGUE ET HABILITATIONS AVP ---

@app.get("/api/rh/avps-disponibles")
def lister_avps_disponibles(user: dict = Security(verifier_utilisateur_rh)):
    if not db:
        raise HTTPException(status_code=500, detail="Firestore non disponible")

    uid_agent = user.get("uid")
    habs_docs = db.collection("habilitations_rh").where("uid_agent", "==", uid_agent).stream()
    statuts_habs = {h.to_dict().get("id_avp"): h.to_dict().get("statut_acces") for h in habs_docs}

    avps_docs = db.collection("avps_disponibles").where("statut", "==", "ouvert").stream()
    
    liste_avps = []
    for doc in avps_docs:
        avp_data = doc.to_dict()
        id_avp = avp_data.get("id_avp", doc.id)
        avp_data["statut_acces_agent"] = statuts_habs.get(id_avp, "non_demande")
        liste_avps.append(avp_data)

    return {"status": "success", "total": len(liste_avps), "avps": liste_avps}

@app.post("/api/rh/demander-acces-avp")
def demander_acces_avp(payload: DemandeAccesModel, user: dict = Security(verifier_utilisateur_rh)):
    if not db:
        raise HTTPException(status_code=500, detail="Firestore non disponible")

    uid_agent = user.get("uid")
    email_agent = user.get("email")
    safe_avp_id = str(payload.id_avp).strip().replace("/", "-").replace(" ", "_")
    id_doc = f"{uid_agent}_{safe_avp_id}"

    doc_ref = db.collection("habilitations_rh").document(id_doc)
    if doc_ref.get().exists:
        return {"status": "already_exists", "message": f"Une demande existe déjà pour l'AVP {payload.id_avp}."}

    doc_ref.set({
        "uid_agent": uid_agent,
        "email_agent": email_agent,
        "id_avp": payload.id_avp,
        "statut_acces": "en_attente",
        "demande_le": firestore.SERVER_TIMESTAMP
    })

    return {"status": "success", "message": f"Demande d'accès pour l'AVP {payload.id_avp} enregistrée."}

@app.get("/api/rh/mes-avps")
def obtenir_mes_avps(user: dict = Security(verifier_utilisateur_rh)):
    if not db:
        raise HTTPException(status_code=500, detail="Firestore non disponible")
    uid_agent = user.get("uid")
    docs = db.collection("habilitations_rh").where("uid_agent", "==", uid_agent).stream()
    return {"status": "success", "habilitations": [d.to_dict() for d in docs]}

# --- 2. CANDIDATURES FILTRÉES ---

@app.get("/api/rh/candidatures")
def lister_candidatures_autorisees(avp_id: Optional[str] = Query(None), user: dict = Security(verifier_utilisateur_rh)):
    if not db:
        raise HTTPException(status_code=500, detail="Firestore non disponible")

    uid_agent = user.get("uid")
    # Support à la fois de "approuve" et "accordee"
    habs = db.collection("habilitations_rh").where("uid_agent", "==", uid_agent).stream()
    avps_autorises = [
        h.to_dict().get("id_avp") for h in habs 
        if h.to_dict().get("statut_acces") in ["approuve", "accordee"]
    ]

    if not avps_autorises:
        return {"agent_connecte": user.get("email"), "total": 0, "candidatures": [], "avps_autorises": [], "message": "Aucun AVP approuvé."}

    if avp_id:
        if avp_id not in avps_autorises:
            raise HTTPException(status_code=403, detail="Accès non autorisé à cet AVP.")
        query_docs = db.collection("candidatures").where("id_avp_cible", "==", avp_id).stream()
    else:
        query_docs = db.collection("candidatures").where("id_avp_cible", "in", avps_autorises[:30]).stream()

    candidatures = []
    for doc in query_docs:
        data = doc.to_dict()
        data["candidature_id"] = doc.id
        candidatures.append(data)

    return {"agent_connecte": user.get("email"), "avps_autorises": avps_autorises, "total": len(candidatures), "candidatures": candidatures}

# --- 3. WORKSPACE MULTI-UPLOAD & VERTEX AI ---

@app.get("/api/rh/candidature/{candidature_id}/documents/{document_index}")
def telecharger_document_candidature(
    candidature_id: str,
    document_index: int,
    user: dict = Security(verifier_utilisateur_rh)
):
    if not db or not storage_client:
        raise HTTPException(status_code=503, detail="Firestore ou Cloud Storage indisponible")

    candidature_doc = db.collection("candidatures").document(candidature_id).get()
    if not candidature_doc.exists:
        raise HTTPException(status_code=404, detail="Candidature introuvable")

    candidature = candidature_doc.to_dict()
    id_avp = candidature.get("id_avp_cible")
    habilitations = db.collection("habilitations_rh").where(
        "uid_agent", "==", user.get("uid")
    ).stream()
    acces_autorise = any(
        habilitation.to_dict().get("id_avp") == id_avp
        and habilitation.to_dict().get("statut_acces") in ["approuve", "accordee"]
        for habilitation in habilitations
    )
    if not acces_autorise:
        raise HTTPException(status_code=403, detail="Accès non autorisé à cet AVP")

    documents = candidature.get("documents_rh_workspace") or []
    if document_index < 0 or document_index >= len(documents):
        raise HTTPException(status_code=404, detail="Document introuvable")

    document = documents[document_index]
    gcs_path = document.get("gcs_path") if isinstance(document, dict) else None
    bucket_prefix = f"gs://{BUCKET_WORKSPACE}/"
    object_prefix = f"workspace/{candidature_id}/"
    if not gcs_path or not gcs_path.startswith(bucket_prefix):
        raise HTTPException(status_code=404, detail="Chemin du document invalide")

    object_name = gcs_path[len(bucket_prefix):]
    if not object_name.startswith(object_prefix) or object_name == object_prefix:
        raise HTTPException(status_code=404, detail="Document introuvable")

    blob = storage_client.bucket(BUCKET_WORKSPACE).blob(object_name)
    try:
        file_contents = blob.download_as_bytes()
    except NotFound:
        raise HTTPException(status_code=404, detail="Fichier absent du stockage")
    except Exception as exc:
        print(f"Erreur de téléchargement GCS pour {candidature_id}: {exc}")
        raise HTTPException(status_code=502, detail="Échec de lecture du fichier dans Cloud Storage")

    filename = os.path.basename(document.get("nom_fichier") or object_name)
    content_type = blob.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return Response(
        content=file_contents,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename, safe='')}",
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )

@app.post("/api/rh/candidature/creer-et-uploader-multiple")
async def creer_et_uploader_multiple(
    id_avp_cible: str = Query(...),
    email_candidat: str = Query(...),
    nom_candidat: Optional[str] = Query(None),
    files: List[UploadFile] = File(...),
    user: dict = Security(verifier_utilisateur_rh)
):
    if not storage_client or not db:
        raise HTTPException(status_code=500, detail="Services GCP indisponibles")

    doc_ref = db.collection("candidatures").document()
    candidature_id = doc_ref.id

    bucket = storage_client.bucket(BUCKET_WORKSPACE)
    documents_meta = []

    for file in files:
        blob_path = f"workspace/{candidature_id}/{file.filename}"
        blob = bucket.blob(blob_path)
        contents = await file.read()
        blob.upload_from_string(contents, content_type=file.content_type)
        
        # Génération d'une URL signée (valide 7 jours) pour téléchargement direct par l'agent RH
        signed_url = ""
        try:
            from google.cloud.storage import Blob
            signed_url = blob.generate_signed_url(version="v4", expiration=604800) # 7 jours
        except Exception:
            signed_url = f"https://storage.googleapis.com/{BUCKET_WORKSPACE}/{blob_path}"

        texte_extrait = ""
        try:
            if file.filename.lower().endswith(('.txt', '.md', '.csv')):
                texte_extrait = contents.decode('utf-8', errors='ignore')
            elif file.filename.lower().endswith('.pdf'):
                texte_extrait = "".join([chr(b) for b in contents if 32 <= b <= 126 or b in (10, 13)])
        except Exception as ex:
            print(f"⚠️ Erreur extraction texte {file.filename}: {ex}")

        documents_meta.append({
            "nom_fichier": file.filename,
            "gcs_path": f"gs://{BUCKET_WORKSPACE}/{blob_path}",
            "download_url": signed_url,
            "texte_extrait": texte_extrait[:4000],
            "ajoute_par": user.get("email")
        })

    candidature_data = {
        "candidature_id": candidature_id,
        "id_avp_cible": id_avp_cible,
        "email": email_candidat,
        "nom_candidat": nom_candidat or email_candidat.split("@")[0],
        "statut_rh": "Nouveau",
        "cree_par": user.get("email"),
        "date_creation": firestore.SERVER_TIMESTAMP,
        "documents_rh_workspace": documents_meta
    }

    doc_ref.set(candidature_data)

    return {
        "status": "success",
        "candidature_id": candidature_id,
        "total_fichiers": len(files),
        "message": f"Candidature créée avec succès ({len(files)} document(s))."
    }

@app.post("/api/rh/candidature/{candidature_id}/analyser")
def analyser_avec_vertex(
    candidature_id: str,
    user: dict = Security(verifier_utilisateur_rh)
):
    if not db or not vertex_client:
        raise HTTPException(status_code=500, detail="Firestore ou Vertex AI indisponible")

    doc_ref = db.collection("candidatures").document(candidature_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Candidature introuvable")

    candidature = doc.to_dict()

    prompt = f"""
    Tu es un expert RH Senior de la Direction des Ressources Humaines de l'OPT-NC.
    Analyse le profil du candidat suivant pour l'AVP : {candidature.get('id_avp_cible', 'AVP OPT-NC')}.

    Données de la candidature et extraits de documents :
    {json.dumps(candidature, default=str, ensure_ascii=False)}

    Retourne STRICTEMENT un objet JSON valide, sans balises markdown (pas de ```json), suivant exactement cette structure :
    {{
      "score_adequation": 85,
      "points_forts": ["3 points forts majeurs du candidat"],
      "points_vigilance": ["2 points de vigilance à vérifier en entretien"],
      "questions_jury": ["3 questions ciblées pour la commission de sélection"],
      "avis_general": "Synthèse globale d'évaluation en 2 phrases."
    }}
    """

    try:
        from google.genai import types
        response = vertex_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        analyse_json = json.loads(raw_text)

        doc_ref.update({
            "analyse_vertex": analyse_json,
            "derniere_analyse_par": user.get("email"),
            "date_analyse": firestore.SERVER_TIMESTAMP
        })

        return {
            "status": "success",
            "candidature_id": candidature_id,
            "analyse_rh": analyse_json
        }
    except Exception as e:
        print(f"❌ Erreur d'analyse Vertex AI : {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse Vertex AI : {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
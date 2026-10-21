# main.py
import io
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from pydantic import BaseModel

from assets_generator import generer_les_quatre_assets
from cloud_storage import sauvegarder_dossier_complet_gcp
from matching_engine import (
    analyser_et_structurer_profil,
    executer_matching_explicable,
)
from pdf_generator import generer_pdf_dossier_candidat
from opt_apigee_client import (
    detail_metier_apigee,
    get_avps_from_apigee,
    get_metiers_from_apigee,
    lister_metiers_apigee,
    rechercher_avps_apigee,
)

app = FastAPI(
    title="Copilote RH API - HackAVP OPT-NC",
    version="2.0.0",
    description="Backend - Ingestion, Matching dynamique (Métiers / AVP), Génération d'Assets, PDF et Double Stockage GCP.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class IngestionRequest(BaseModel):
    description_brute: str


class MatchingRequest(BaseModel):
    profil_structurer: str | dict
    id_avp_cible: str | None = None
    source_matching: str = "avps"  # "avps" (opt_avps_disponibles) ou "metiers" (opt_metiers)


class AssetsRequest(BaseModel):
    profil_structurer: str | dict
    id_avp_cible: str = "Poste Standard OPT-NC"
    choix_utilisateur: dict = None
    donnees_candidat_raw: dict = None


class PostulerRequest(BaseModel):
    email: str
    profil_structurer: str | dict
    id_avp_cible: str = "Poste Standard OPT-NC"
    choix_utilisateur: dict = None
    donnees_candidat_raw: dict = None


class AvpSearchRequest(BaseModel):
    prompt: str = None
    filters: dict = None
    top_k: int = 5


@app.get("/")
def read_root():
    return {"status": "online", "project": "HackAVP Copilote RH - OPT-NC", "version": "2.0.0"}


@app.post("/api/candidat/ingestion")
async def api_ingestion_profil(
    description_brute: str = Form(None),
    files: list[UploadFile] = File(None),
    file: UploadFile = File(None),
):
    """
    FONCTION ① : Ingestion de plusieurs fichiers (PDF/TXT) et extraction combinée via pypdf.
    """
    try:
        texte = ""
        liste_fichiers = []
        if files:
            liste_fichiers.extend(files)
        if file:
            liste_fichiers.append(file)

        if liste_fichiers:
            for f in liste_fichiers:
                contents = await f.read()
                if f.filename.lower().endswith(".pdf") or "pdf" in f.content_type:
                    reader = PdfReader(io.BytesIO(contents))
                    for page in reader.pages:
                        texte += (page.extract_text() or "") + "\n"
                else:
                    texte += contents.decode("utf-8", errors="ignore") + "\n"
        elif description_brute:
            texte = description_brute
        else:
            raise HTTPException(status_code=400, detail="Aucun texte ou fichier fourni")

        result_json = analyser_et_structurer_profil(texte)
        return {"fonction": "1 - Ingestion Profil", "resultat": result_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/candidat/matching")
def api_matching_explicable(payload: MatchingRequest):
    """
    FONCTION ② : Matching explicable basé sur le croisement profil / Apigee.
    Permet de choisir dynamiquement entre 'avps' (opt_avps_disponibles) et 'metiers' (opt_metiers).
    """
    try:
        # Passage du paramètre source_matching au moteur de matching
        result_json = executer_matching_explicable(
            profil_structurer=payload.profil_structurer,
            id_avp_cible=payload.id_avp_cible,
            source_matching=payload.source_matching
        )
        return {
            "fonction": "2 - Matching Explicable",
            "source_utilisee": payload.source_matching,
            "resultat": result_json
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/candidat/assets")
def api_generer_assets(payload: AssetsRequest):
    """
    FONCTION ③ : Génération automatique des 4 assets Gemini (CV, Lettre, Bilan, Entretien)
    + Injections et fusions PDF (Fiche de renseignements & Attestation).
    """
    try:
        result_json = generer_les_quatre_assets(
            profil_structurer=payload.profil_structurer,
            id_avp_cible=payload.id_avp_cible,
            choix_utilisateur=payload.choix_utilisateur,
            donnees_candidat_raw=payload.donnees_candidat_raw,
        )
        return {"fonction": "3 - Génération des Assets & PDF Officiels", "resultat": result_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/candidat/telecharger-pdf")
def api_telecharger_pdf_dossier(payload: PostulerRequest):
    """
    ÉTAPE 4 : Permet au candidat de télécharger son dossier complet de candidature au format PDF.
    """
    try:
        # 1. Génération préalable des assets et contenus via Gemini
        assets_res = generer_les_quatre_assets(
            profil_structurer=payload.profil_structurer,
            id_avp_cible=payload.id_avp_cible,
            choix_utilisateur=payload.choix_utilisateur,
            donnees_candidat_raw=payload.donnees_candidat_raw,
        )

        # 2. Génération du fichier PDF récapitulatif
        pdf_bytes = generer_pdf_dossier_candidat(assets_res)

        nom_candidat = "Candidat"
        if payload.donnees_candidat_raw and "nom" in payload.donnees_candidat_raw:
            nom_candidat = payload.donnees_candidat_raw["nom"].replace(" ", "_")

        filename = f"Dossier_Candidature_{nom_candidat}_{payload.id_avp_cible.replace('/', '-')}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de génération du PDF : {str(e)}")


@app.post("/api/candidat/postuler")
def api_postuler_candidature(payload: PostulerRequest):
    """
    FONCTION ④ : Soumission finale - Génération des assets, des PDF et double archivage Cloud (Firestore & Google Cloud Storage).
    """
    try:
        # 1. Génération des assets par Gemini + PDF par ReportLab
        assets_res = generer_les_quatre_assets(
            profil_structurer=payload.profil_structurer,
            id_avp_cible=payload.id_avp_cible,
            choix_utilisateur=payload.choix_utilisateur,
            donnees_candidat_raw=payload.donnees_candidat_raw,
        )

        # 2. Sauvegarde centralisée (GCS + Firestore)
        stockage_res = sauvegarder_dossier_complet_gcp(
            email=payload.email,
            profil_structurer=payload.profil_structurer,
            id_avp_cible=payload.id_avp_cible,
            assets_result=assets_res,
        )

        return {
            "fonction": "4 - Soumission & Stockage Double GCP",
            "stockage": stockage_res,
            "resultat_assets": assets_res,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# Endpoints Apigee OPT-NC
# =====================================================================
@app.get("/api/apigee/metiers")
def api_get_metiers(famille: str = None, actif: bool = None, statut: str = None):
    return lister_metiers_apigee(famille=famille, actif=actif, statut=statut)


@app.get("/api/apigee/metiers/{code_metier}")
def api_get_metier_detail(code_metier: str):
    return detail_metier_apigee(code_metier)


@app.post("/api/apigee/avps/search")
def api_search_avps(payload: AvpSearchRequest):
    return rechercher_avps_apigee(prompt=payload.prompt, filters=payload.filters, top_k=payload.top_k)
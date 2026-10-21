# cloud_storage.py
import json
import os
from google.cloud import firestore, storage

try:
    db = firestore.Client()
    storage_client = storage.Client()
except Exception as e:
    db = None
    storage_client = None
    print(f"⚠️ Avertissement GCP : {e}")

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

def sauvegarder_dossier_complet_gcp(email: str, profil_structurer, id_avp_cible: str, assets_result: dict):
    if not db:
        return {"status": "error", "message": "Firestore non initialisé"}

    try:
        doc_ref = db.collection("candidatures").document()
        candidature_id = doc_ref.id

        # Sauvegarde des fichiers sur Cloud Storage si possible
        gcs_urls = {}
        if storage_client and BUCKET_NAME:
            try:
                bucket = storage_client.bucket(BUCKET_NAME)
                for asset_name, content in assets_result.items():
                    blob_path = f"candidatures/{candidature_id}/{asset_name}.json"
                    blob = bucket.blob(blob_path)
                    content_str = json.dumps(content, ensure_ascii=False, indent=2) if isinstance(content, (dict, list)) else str(content)
                    blob.upload_from_string(content_str, content_type="application/json")
                    gcs_urls[asset_name] = f"gs://{BUCKET_NAME}/{blob_path}"
            except Exception as st_err:
                print(f"Note GCS : {st_err}")
        elif not BUCKET_NAME:
            print("Bucket GCS non configuré : les fichiers ne seront pas téléversés.")

        # Enregistrement structuré dans Firestore
        payload = {
            "candidature_id": candidature_id,
            "email": email,
            "id_avp_cible": id_avp_cible,
            "profil_structurer": profil_structurer,
            "assets": assets_result,
            "gcs_urls": gcs_urls,
            "statut": "NOUVEAU",
            "date_depot": firestore.SERVER_TIMESTAMP
        }

        doc_ref.set(payload)

        return {
            "status": "success",
            "candidature_id": candidature_id,
            "message": f"Dossier enregistré pour {email} (Firestore + GCS)"
        }

    except Exception as e:
        return {"status": "error", "detail": str(e)}

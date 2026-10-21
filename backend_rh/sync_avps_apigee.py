import os
import json
from datetime import datetime, timezone, timedelta
from google.cloud import firestore
from opt_apigee_client import rechercher_avps_apigee

PROJECT_ID = os.getenv("GCP_PROJECT")
DATABASE_ID = os.getenv("FIRESTORE_DATABASE")

db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

def nettoyer_avps_expires():
    """Supprime de Firestore les AVP dont la date de clôture est dépassée."""
    print("🧹 Vérification des AVP périmés pour suppression...")
    maintenant = datetime.now(timezone.utc)
    
    expires_docs = db.collection("avps_disponibles").where("date_cloture", "<", maintenant).stream()
    
    batch = db.batch()
    supp_compteur = 0
    for doc in expires_docs:
        print(f"   🗑️ Suppression de l'AVP expiré : {doc.id}")
        batch.delete(doc.reference)
        supp_compteur += 1
        
    if supp_compteur > 0:
        batch.commit()
        print(f"✅ {supp_compteur} AVP périmés supprimés de la base.")
    else:
        print("✨ Aucun AVP expiré à supprimer.")

def synchroniser_avps():
    nettoyer_avps_expires()
    
    NOMBRE_MAX_AVP = 50
    print(f"🔄 Connexion à l'API Apigee pour récupérer jusqu'à {NOMBRE_MAX_AVP} AVP...")
    
    resultat = rechercher_avps_apigee(top_k=NOMBRE_MAX_AVP)
    if "error" in resultat:
        print(f"❌ Erreur lors de la récupération : {resultat}")
        return

    avps = resultat if isinstance(resultat, list) else resultat.get("results", resultat.get("avps", resultat.get("data", [])))
    if not avps:
        print("⚠️ Aucun AVP retourné par l'API.")
        return

    batch = db.batch()
    compteur = 0
    date_cloture_secours = datetime.now(timezone.utc) + timedelta(days=30)

    for idx, avp in enumerate(avps):
        if not isinstance(avp, dict):
            continue

        brut_id = avp.get("id_avp") or avp.get("id") or avp.get("code_avp") or f"AVP-2026-00{idx+1}"
        id_avp = str(brut_id).strip().replace("/", "-").replace(" ", "_")

        # 🧠 Extraction et parsing du champ 'json_data' s'il existe pour aller chercher les détails schema.org
        details_schema = {}
        raw_json_data = avp.get("json_data")
        if raw_json_data:
            try:
                if isinstance(raw_json_data, str):
                    details_schema = json.loads(raw_json_data)
                elif isinstance(raw_json_data, dict):
                    details_schema = raw_json_data
            except Exception:
                pass

        # 📅 Récupération de la vraie date de clôture (validThrough) depuis le schema.org ou secours à J+30
        date_cloture_str = details_schema.get("validThrough")
        date_cloture = date_cloture_secours
        if date_cloture_str:
            try:
                # Format attendu généralement YYYY-MM-DD
                date_cloture = datetime.fromisoformat(date_cloture_str.replace("Z", "+00:00"))
                if date_cloture.tzinfo is None:
                    date_cloture = date_cloture.replace(tzinfo=timezone.utc)
            except Exception:
                pass

        doc_ref = db.collection("avps_disponibles").document(id_avp)
        
        # Structuration propre pour Firestore et ton Copilote RH
        avp_data = {
            "id_avp": str(brut_id),
            "intitule": avp.get("titre") or details_schema.get("title") or f"Poste {id_avp}",
            "direction": avp.get("direction") or details_schema.get("hiringOrganization", {}).get("name", "DRH OPT-NC"),
            "famille_metier": ", ".join(avp.get("familles", ["Télécoms / SI"])) if isinstance(avp.get("familles"), list) else "Télécoms / SI",
            "ville": avp.get("ville", "Nouméa"),
            "province": avp.get("province", "Province Sud"),
            "nb_agents_encadres": avp.get("nb_agents_encadres", 0),
            "description": details_schema.get("description", ""),
            "competences_requises": details_schema.get("educationRequirements", {}).get("competencyRequired", []),
            "soft_skills": details_schema.get("skills", []),
            "statut": "ouvert",
            "date_cloture": date_cloture,
            "synchro_apigee_le": firestore.SERVER_TIMESTAMP,
            "details_bruts": avp
        }
        
        batch.set(doc_ref, avp_data, merge=True)
        compteur += 1
        print(f"   ➕ AVP synchronisé et enrichi : {id_avp} (Clôture : {date_cloture.strftime('%Y-%m-%d')})")

    batch.commit()
    print(f"🎉 Synchronisation terminée : {compteur} AVP actifs et enrichis enregistrés dans Firestore.")

if __name__ == "__main__":
    synchroniser_avps()
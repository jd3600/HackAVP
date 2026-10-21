# Copilote RH OPT+ — dossier de présentation

Cette copie rassemble les éléments utiles à l'examen du prototype par un jury :
le parcours candidat, l'espace RH, les deux API, les modèles PDF et les supports
de présentation. Les anciennes pages d'essai, les fichiers compilés et les
configurations de déploiement ont été écartés.

> **Prototype de démonstration.** L'IA fournit des suggestions, pas une décision
> de recrutement. Les résultats doivent être vérifiés par une personne. Utilisez
> uniquement des données fictives pendant la démonstration.

## Contenu

| Dossier | Rôle |
| --- | --- |
| `frontend/` | Interface de démonstration candidat |
| `backend/` | API candidat : ingestion, rapprochement, génération de documents |
| `frontend_rh/` | Interface de démonstration RH |
| `backend_rh/` | API RH : habilitations, dossiers et analyse assistée |
| `docs/PITCH_PRESENTATION.md` | Pitch oral court et version 2 minutes |
| `docs/SYNTHESE_PROJET.md` | Proposition de valeur, parcours et limites |

## Démarrage local — parcours candidat

Prérequis : Python 3.10 ou plus récent. Depuis la racine de ce dossier, ouvrez
un terminal et lancez l'API :

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Dans un second terminal, servez l'interface statique :

```bash
cd frontend
python -m http.server 5500
```

Ouvrez ensuite <http://localhost:5500>. La documentation interactive de l'API
est disponible à <http://localhost:8000/docs>.

Les dépendances sont installées depuis PyPI et certaines ressources visuelles
proviennent de CDN : une connexion Internet est nécessaire.

### Services externes du parcours candidat

L'API démarre sans fichier de configuration local, mais les appels d'IA et les
connexions aux services externes nécessitent des accès autorisés. Les valeurs
ne sont volontairement pas incluses dans ce dossier.

- `GOOGLE_API_KEY` : génération et analyse via Google GenAI.
- `OPT_API_KEY` : accès à l'API OPT-NC lorsqu'une clé est requise.
- Identifiants Google Cloud Application Default Credentials et, si utilisés,
  `GCP_PROJECT` et `GCS_BUCKET_NAME` : persistance Firestore / Cloud Storage.

Fournissez ces paramètres uniquement dans l'environnement local ou le gestionnaire
de secrets autorisé. Ne les ajoutez ni au code, ni à un dépôt, ni aux supports du
jury. Sans accès configuré, les écrans et la documentation restent consultables,
mais les fonctions connectées ne sont pas garanties.

## Espace RH

L'interface RH est disponible dans `frontend_rh/`. Le fichier
`frontend_rh/config.local.js` est volontairement vide de toute valeur sensible.
Renseignez-y les paramètres Firebase du projet de démonstration autorisé et
l'URL locale ou de démonstration du backend RH. Ce fichier est ignoré par Git.
Sans configuration Firebase, l'interface affiche un message explicite au lieu
de tenter une connexion.

Pour lancer l'API RH, installez ses dépendances dans un environnement Python
séparé puis exécutez, depuis `backend_rh/` :

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8080
```

Le service RH nécessite également Firebase Authentication, les identifiants
Google Cloud et les paramètres autorisés `GCP_PROJECT`, `FIRESTORE_DATABASE`,
`GCS_BUCKET_CANDIDATS` et `GCS_BUCKET_WORKSPACE`. Ces intégrations ne sont pas
simulées : sans elles, les opérations RH protégées ne fonctionneront pas.



## Limites à signaler

- Il s'agit d'un prototype, le système est sujet a des améliorations 
  et nous sommes prêts a entendre toutes suggestions .
- La qualité des suggestions dépend des données d'entrée, du référentiel OPT-NC
  et de la disponibilité des services tiers.
- Les données de candidature sont sensibles : ne chargez aucun dossier réel
  pendant une présentation sans autorisation, information des personnes et
  cadre de traitement validé.
- La copie est délibérément livrée sans clé, identifiant de projet, fichier `.env`
  ni URL de déploiement préconfigurée.

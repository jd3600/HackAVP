# Copilote RH OPT-NC — synthèse marketing

## 1. Le projet en bref

Le Copilote RH est un prototype d’assistance au recrutement conçu autour des avis de vacance de poste (AVP) et des référentiels métiers de l’OPT-NC. Il met en relation deux publics :

- **Les candidats**, qui peuvent structurer leur profil, explorer des métiers ou des AVP pertinents et préparer des éléments de candidature.
- **Les équipes RH**, qui peuvent consulter les AVP, gérer les accès à leur espace de travail et examiner les dossiers reçus avec une aide de l’IA.

La proposition de valeur centrale est de **rendre le parcours de recrutement plus lisible et de réduire les tâches de préparation et de traitement des candidatures**, tout en laissant les décisions aux personnes concernées.

## 2. Notions marketing appliquées au projet

### Proposition de valeur

La proposition de valeur décrit le problème auquel le service répond et le bénéfice qu’il apporte.

- **Côté candidat :** comprendre les rapprochements possibles entre son profil et les besoins de l’OPT-NC, repérer ses atouts et ses écarts, et préparer plus facilement son dossier.
- **Côté RH :** centraliser les dossiers associés aux AVP, retrouver les documents utiles et obtenir une première synthèse pour faciliter leur examen.
- **Pour l’organisation :** proposer une expérience numérique plus cohérente entre le catalogue de postes, les candidatures et leur traitement.

Il s’agit d’une assistance à la préparation et à l’analyse, et non d’une promesse d’embauche, de sélection automatique ou de réduction garantie des délais.

### Segmentation et publics cibles

La segmentation consiste à adapter le service et son message aux besoins de groupes différents.

| Public | Besoin principal | Bénéfice à mettre en avant |
|---|---|---|
| Candidat en recherche d’un poste | Repérer des pistes adaptées à son expérience | Un rapprochement expliqué avec les métiers ou AVP disponibles |
| Candidat préparant une candidature | Organiser les informations et documents | Une aide à la rédaction et à la préparation du dossier |
| Agent ou recruteur RH | Consulter les dossiers d’un AVP autorisé | Un espace de travail regroupant dossiers, documents et analyses |
| Responsable RH | Harmoniser les pratiques et suivre le traitement | Un processus plus structuré, à évaluer avec des indicateurs opérationnels |

Ces segments sont des publics fonctionnels identifiés à partir des interfaces du prototype. Ils ne constituent pas, à eux seuls, une étude de marché ou une validation des besoins utilisateurs.

### Parcours utilisateur et expérience de service

Le parcours candidat visible dans l’application suit quatre étapes :

1. **Ingestion du profil** : dépôt de documents ou saisie de texte.
2. **Exploration et matching** : comparaison avec le référentiel métiers ou les AVP ouverts, avec affichage d’un score estimé et d’explications.
3. **Préparation** : génération de contenus tels qu’un CV orienté, une lettre, un bilan des écarts, une préparation à l’entretien et des formulaires PDF disponibles.
4. **Soumission et archivage** : envoi du dossier et stockage dans les services cloud prévus par le backend.

Le parcours RH complète ce dispositif : connexion, consultation du catalogue d’AVP, demande d’accès à un AVP, consultation des candidatures autorisées, téléversement de documents et lancement d’une analyse assistée.

En marketing de service, ce parcours compte autant que la fonctionnalité : la clarté des étapes, les consignes de dépôt, les messages d’erreur et l’explication de l’usage des données influencent la confiance et l’adoption.

### Positionnement et différenciation

Le positionnement possible est celui d’un **assistant de recrutement spécialisé dans le contexte des métiers, des AVP et des formulaires de l’OPT-NC**, plutôt qu’un outil généraliste de rédaction.

Les éléments différenciants visibles dans le projet sont :

- le choix entre un référentiel de métiers et des AVP ;
- des rapprochements accompagnés d’explications, de points forts et d’écarts à combler ;
- la génération de contenus adaptés à un poste ciblé ;
- la prise en compte de formulaires de candidature officiels ;
- un espace RH dont l’accès aux dossiers est associé aux habilitations sur les AVP.

Ces éléments décrivent le produit tel qu’il est conçu dans le code ; leur efficacité et leur valeur perçue doivent être confirmées par des essais auprès de candidats et de professionnels RH.

### Confiance, preuve et responsabilité

La confiance est un enjeu marketing important puisque le service traite des profils et des candidatures. Le moteur présente le score comme une **estimation d’aide à la décision** et demande de ne pas inventer de poste lorsque les données de référence sont insuffisantes. Les explications du rapprochement soutiennent la transparence, mais ne rendent pas le résultat infaillible ni nécessairement objectif.

Pour communiquer de façon responsable, il convient de :

- présenter l’IA comme une aide, sans prétendre qu’elle choisit ou évalue parfaitement les personnes ;
- encourager la vérification et la modification des textes générés avant leur utilisation ;
- préciser les finalités du traitement, les durées de conservation et les modalités d’accès aux données ;
- limiter les données collectées à ce qui est utile et protéger les documents de candidature ;
- vérifier les règles d’accès, la sécurité et la conformité applicables avant tout déploiement réel.

L’interface RH et son backend intègrent une authentification Firebase et des vérifications d’accès par AVP. Cela ne suffit pas, à lui seul, à démontrer la conformité complète, la sécurité de toute l’architecture ou la validité juridique d’un déploiement.

## 3. Messages marketing possibles

Ces formulations sont des pistes de communication à valider avec l’OPT-NC :

- **Pour les candidats :** « Explorez les métiers et AVP qui correspondent à votre parcours, comprenez les rapprochements proposés et préparez votre candidature étape par étape. »
- **Pour les équipes RH :** « Retrouvez les dossiers liés à vos AVP et appuyez-vous sur une première analyse pour faciliter leur examen. »
- **Promesse commune :** « Une aide numérique pour rendre le recrutement plus clair et mieux structuré. »

Le ton recommandé est informatif, accessible et rassurant. Il doit éviter les expressions telles que « candidat idéal garanti », « sélection objective » ou « candidature automatiquement optimisée », qui laisseraient entendre des résultats que le prototype ne garantit pas.

## 4. Indicateurs marketing et d’adoption à suivre

Des indicateurs permettent de vérifier si la proposition de valeur répond effectivement aux besoins :

- **Adoption** : nombre d’utilisateurs candidats et RH actifs, par période et par parcours ;
- **Activation** : part des utilisateurs qui terminent l’ingestion, consultent un résultat ou déposent un dossier ;
- **Conversion du parcours** : proportion de profils analysés qui passent à la préparation puis à la soumission ;
- **Abandon** : étape à laquelle les utilisateurs interrompent le parcours et raisons déclarées ;
- **Qualité perçue** : satisfaction sur la pertinence des rapprochements, la clarté des explications et l’utilité des documents générés ;
- **Efficacité RH** : temps consacré au tri et à l’examen des dossiers, mesuré avant et après expérimentation ;
- **Confiance et accessibilité** : compréhension du rôle de l’IA, facilité d’usage et capacité à corriger ou contester un résultat.

Ces indicateurs devraient être évalués avec un protocole de test, des retours qualitatifs et des règles de protection des données. Un score de matching ou un volume de candidatures ne constitue pas, à lui seul, une preuve de qualité ou d’équité.

## 5. Correspondance avec les dossiers du projet

- [`backend/`](../backend/) : API du parcours candidat, extraction de texte PDF/TXT, structuration du profil avec Gemini, matching explicable avec les API métiers/AVP, génération de contenus et de PDF, puis archivage via Firestore et Cloud Storage.
- [`frontend/`](../frontend/) : interface candidat en quatre étapes, dépôt de fichiers, sélection de la source du matching, consultation des explications, préparation et soumission du dossier.
- [`backend_rh/`](../backend_rh/) : API de l’espace RH, authentification Firebase, accès aux candidatures selon les habilitations AVP, téléversement de documents, stockage cloud et analyse assistée par Vertex AI.
- [`frontend_rh/`](../frontend_rh/) : interface recruteur pour se connecter, consulter les AVP, demander ou ouvrir un espace autorisé, téléverser des dossiers et lancer l’analyse.

Les dossiers décrivent un prototype logiciel. Les promesses marketing doivent être confirmées par des tests utilisateurs et les contrôles opérationnels, juridiques et de sécurité requis avant une mise en production.

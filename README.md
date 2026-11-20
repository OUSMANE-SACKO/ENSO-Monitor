# ENSO Monitor

Application web de consultation et de comparaison historique de l'indice
**NOAA ONI** (*Oceanic Niño Index*) pour la région Niño 3.4.

Le projet transforme la série NOAA en observations traçables, les expose avec
une API FastAPI et les présente dans un tableau de bord React/TypeScript.

## Sommaire

- [Périmètre](#périmètre)
- [Démarrage rapide avec Docker](#démarrage-rapide-avec-docker)
- [Données et provenance](#données-et-provenance)
- [API](#api)
- [Installation sans conteneuriser l'application](#installation-sans-conteneuriser-lapplication)
- [Tests et vérifications](#tests-et-vérifications)
- [Structure du dépôt](#structure-du-dépôt)
- [Sécurité et limites](#sécurité-et-limites)
- [Utilisation de l'IA](#utilisation-de-lia)

## Périmètre

Le MVP permet de :

1. importer la série NOAA ONI dans PostgreSQL avec provenance et gestion des
   doublons;
2. consulter les observations avec des filtres temporels;
3. visualiser l'anomalie ONI dans une courbe filtrable;
4. comparer deux périodes mensuelles à partir des mesures disponibles.

La comparaison fournit le nombre d'observations, la moyenne, le maximum et le
minimum de chaque période, puis une interprétation descriptive accompagnée de
limites. Les périodes sont choisies par l'utilisateur : l'application ne
classe pas automatiquement les phases ENSO et ne produit pas de prévision.

## Prérequis

- Docker avec Docker Compose pour démarrer la stack complète.
- Python 3.11 ou supérieur pour lancer le backend et les tests hors Docker.
- Node.js 22.22.2+, 24.15+ ou 26+ avec npm pour lancer le frontend hors Docker.
- Accès réseau pour télécharger la série NOAA.

## Démarrage rapide avec Docker

### Prérequis

- Docker avec Docker Compose.
- Une connexion réseau pour télécharger la série NOAA.

Depuis la racine du dépôt :

```bash
docker compose up --build -d
docker compose ps
```

Le service API applique les migrations Alembic au démarrage. Quand les services
sont sains, ouvrir :

- Interface : <http://localhost:5173>
- Documentation interactive de l'API : <http://localhost:8000/docs>

Le premier démarrage ne télécharge pas automatiquement les données. Pour
importer la série NOAA, fournir explicitement la version indiquée par NOAA :

```bash
docker compose --profile tools run --build --rm etl \
  python -m etl.run --version "NOAA ONI v6 (AAAA-MM-JJ)"
```

Remplacer `AAAA-MM-JJ` par la date réelle de l'extraction et adapter la version
si NOAA l'indique autrement. Le script affiche les compteurs d'import. Une
réexécution n'insère pas de doublons et peut mettre à jour des valeurs révisées
par NOAA.

### Commandes Docker utiles

```bash
docker compose ps                    # état et santé des services
docker compose logs -f api           # journaux de l'API
docker compose logs -f frontend      # journaux du frontend
docker compose logs -f db            # journaux PostgreSQL
docker compose down                 # arrêter sans supprimer les données
```

Les services utilisent le volume persistant `pgdata`. **Ne pas ajouter `-v` à
`docker compose down`** sauf si l'objectif est de supprimer les données.
Les identifiants `enso/enso` définis dans [compose.yaml](compose.yaml) sont
réservés au développement local; ne pas les réutiliser en production.

### Services

| Service | Rôle | Adresse locale |
| --- | --- | --- |
| `db` | PostgreSQL 16 et volume `pgdata` | `localhost:5432` |
| `api` | FastAPI, migrations et documentation OpenAPI | `localhost:8000` |
| `frontend` | Build React servi par Nginx; proxy `/api/` vers l'API | `localhost:5173` |
| `etl` | Import ponctuel NOAA, activé par le profil `tools` | lancé avec `docker compose run` |

Le service ETL est ponctuel : il ne télécharge pas la série à chaque démarrage
de l'application.

## Données et provenance

- Indice : **ONI uniquement**; ONI et RONI ne sont pas interchangeables.
- Organisme : NOAA Climate Prediction Center (CPC).
- Page de référence : [NOAA CPC — ONI](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/index.php).
- Fichier utilisé par défaut : [`oni.ascii.txt`](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt).
- URL configurable avec `ONI_URL`.

L'ETL exige l'option `--version` afin de conserver la version déclarée par
l'opérateur. Chaque import enregistre notamment la source, la date
`extracted_at`, l'empreinte SHA-256 du fichier et le nombre de lignes lues,
insérées, mises à jour ou rejetées.

L'ONI est une anomalie de température de surface de la mer calculée comme une
moyenne glissante sur trois mois pour Niño 3.4. La saison NOAA est conservée et
la période est datée au premier jour du mois central. La comparaison porte
uniquement sur les observations disponibles; les mois manquants ne sont pas
interpolés.

## API

Toutes les routes applicatives sont sous `/api/v1`. La documentation complète
et les schémas sont disponibles sur <http://localhost:8000/docs>.

### Observations

```http
GET /api/v1/observations
GET /api/v1/observations?start_date=1997-01-01&end_date=1998-12-01
```

`start_date` et `end_date` sont facultatives, au format `AAAA-MM-JJ`, et
inclusives. La réponse est classée chronologiquement et contient `period`,
`season`, `total` et `anomaly`. Une date invalide ou un début postérieur à la
fin retourne HTTP `422`.

### Comparaison

```http
GET /api/v1/comparisons?first_start_date=1997-01-01&first_end_date=1998-12-01&second_start_date=2010-01-01&second_end_date=2011-12-01
```

Les quatre paramètres sont obligatoires et doivent désigner le premier jour du
mois. La réponse contient les statistiques de chaque plage, l'écart de moyenne,
une interprétation écrite et les limites à considérer. Des dates invalides
retournent `422`; si au moins une période ne contient aucune observation,
l'API retourne `404`.

## Installation sans conteneuriser l'application

Cette méthode lance PostgreSQL avec Docker, puis l'API et Vite directement sur
la machine. **Ne pas lancer les API hôte et conteneur simultanément**, car
elles utilisent toutes deux le port `8000`.

### Backend et base de données

Depuis la racine du dépôt :

```bash
docker compose up -d db
cd backend
python -m venv .venv
source .venv/bin/activate             # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                  # Windows : copy .env.example .env
alembic upgrade head
python -m etl.run --version "NOAA ONI v6 (AAAA-MM-JJ)"
```

Pour importer un fichier téléchargé manuellement, depuis `backend/` :

```bash
python -m etl.run --version "<version NOAA>" --file data/oni.ascii.txt
```

Lancer ensuite l'API dans ce terminal :

```bash
uvicorn app.main:app --reload
```

### Frontend

Dans un autre terminal, depuis la racine du dépôt :

```bash
cd frontend
npm ci
cp .env.example .env                 # Windows : copy .env.example .env
npm run dev
```

Ouvrir <http://localhost:5173>. Par défaut, `VITE_API_BASE_URL` pointe vers
`http://localhost:8000`; le serveur Vite dispose aussi d'un proxy `/api` pour
le développement.

### Variables d'environnement

| Variable | Fichier | Description |
| --- | --- | --- |
| `DATABASE_URL` | `backend/.env` | URL PostgreSQL du backend/ETL; en local, hôte `localhost`. |
| `ONI_URL` | `backend/.env` | URL du fichier NOAA téléchargé par défaut. |
| `CORS_ORIGINS` | `backend/.env` | Origines autorisées, séparées par des virgules. |
| `VITE_API_BASE_URL` | `frontend/.env` | URL de l'API utilisée par le navigateur. |
| `TEST_DATABASE_URL` | `backend/.env.example` | Réservée à d'éventuels tests d'intégration; les tests actuels ne l'utilisent pas. |

Les valeurs d'exemple sont locales au développement. Ne pas commiter de
secrets ni de fichiers `.env`.

## Tests et vérifications

### Tests automatisés

Backend, depuis `backend/` avec l'environnement virtuel activé :

```bash
python -m pytest
```

Frontend, depuis `frontend/` :

```bash
npm test
npm run lint
npm run build
```

La suite backend couvre la transformation NOAA et les routes API. Les tests
API remplacent la session SQLAlchemy : ils ne constituent pas à eux seuls un
test d'intégration avec PostgreSQL. Le test frontend vérifie que changer la
période met à jour les données et le nombre de points du graphique.

### Vérification intégrée

Le 20 novembre 2026, l'ETL a téléchargé la série NOAA et importé 921 lignes dans
une base Docker locale vide : 921 insertions, aucune mise à jour ni ligne
rejetée au premier import. L'API et l'interface ont ensuite été vérifiées sur
ces données; le filtre janvier 1997–décembre 1998 retourne 24 observations.
Ces chiffres décrivent cette extraction et peuvent évoluer lorsque NOAA révise
la série.

## Structure du dépôt

```text
.
├── compose.yaml
├── backend/
│   ├── app/                 # FastAPI, modèles, schémas et logique métier
│   │   └── api/v1/          # Routes versionnées observations/comparaison
│   ├── etl/                 # Extraction, transformation et chargement ONI
│   ├── alembic/             # Migrations PostgreSQL
│   └── tests/               # Tests de transformation et d'API
└── frontend/
    ├── src/                 # React, filtres, graphique et tests
    ├── Dockerfile
    └── nginx.conf           # Fichiers statiques et proxy /api/
```

## Sécurité et limites

- L'API du MVP est en lecture seule et ne propose pas de compte administrateur.
- Les paramètres sont validés par FastAPI; SQLAlchemy exécute des requêtes
  paramétrées.
- CORS est configurable par environnement.
- Les identifiants inclus dans Compose sont exclusivement destinés au
  développement local.
- Le Compose actuel ne fournit ni Caddy ni configuration de production. Aucun
  déploiement public ou VPS n'est requis ou revendiqué.
- L'indice ONI seul ne décrit pas les impacts climatiques régionaux, les causes
  d'un épisode ou son évolution future.

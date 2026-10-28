# ENSO Monitor

Explorer l'indice NOAA ONI (El Niño / La Niña).

## Étape 1 : import des données (ETL)

```bash
docker compose up -d db                 # PostgreSQL local
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head                    # crée les tables
python -m pytest tests/test_transform.py
```

Télécharger le fichier NOAA : https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
(noter la date et la version indiquée sur la page ONI), le placer dans `backend/data/`, puis :

```bash
python -m etl.run --version "<version NOAA>" --file data/oni.ascii.txt
```

Ou directement depuis NOAA : `python -m etl.run --version "<version NOAA>"`

Relancer l'import ne crée aucun doublon.

"""Chargement des lignes propres dans PostgreSQL, avec traçabilité."""
import hashlib

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import ClimateIndex, Import, Observation, Source

ONI_META = {
    "code": "ONI",
    "name": "Oceanic Niño Index",
    "unit": "°C",
    "description": "Anomalie de température de surface de la mer, région Niño 3.4 "
    "(5°N-5°S, 120°-170°W), moyenne glissante sur 3 mois.",
}


def get_or_create(session: Session, model, lookup: dict, defaults: dict | None = None):
    obj = session.scalar(select(model).filter_by(**lookup))
    if obj is None:
        obj = model(**lookup, **(defaults or {}))
        session.add(obj)
        session.flush()  # obtient l'id sans valider la transaction
    return obj


def load_oni(
    session: Session,
    clean: pd.DataFrame,
    *,
    raw_text: str,
    source_url: str,
    source_version: str,
    rows_read: int,
    rows_rejected: int,
) -> Import:
    """Insère les observations dans UNE transaction : tout passe ou rien ne passe.

    Doublons avec la base : contrainte UNIQUE (index_id, period) + ON CONFLICT.
    - mois absent       -> inséré
    - mois déjà présent, valeur identique -> ignoré
    - mois déjà présent, valeur différente (révision NOAA) -> mis à jour
    """
    index = get_or_create(session, ClimateIndex, {"code": ONI_META["code"]},
                          {k: v for k, v in ONI_META.items() if k != "code"})
    source = get_or_create(session, Source, {"url": source_url, "version": source_version},
                           {"provider": "NOAA CPC"})

    run = Import(
        source_id=source.id,
        file_sha256=hashlib.sha256(raw_text.encode()).hexdigest(),
        rows_read=rows_read,
        rows_rejected=rows_rejected,
    )
    session.add(run)
    session.flush()

    count_before = session.scalar(
        select(func.count()).select_from(Observation).where(Observation.index_id == index.id)
    )

    rows = [
        {
            "index_id": index.id,
            "import_id": run.id,
            "period": r.period,
            "season": r.season,
            "total": float(r.total),
            "anomaly": float(r.anomaly),
        }
        for r in clean.itertuples(index=False)
    ]

    changed = 0
    if rows:
        stmt = insert(Observation).values(rows)  # requête paramétrée, pas de SQL concaténé
        stmt = stmt.on_conflict_do_update(
            constraint="uq_observation_index_period",
            set_={
                "total": stmt.excluded.total,
                "anomaly": stmt.excluded.anomaly,
                "season": stmt.excluded.season,
                "import_id": stmt.excluded.import_id,
            },
            # ne touche la ligne QUE si la valeur a changé
            where=(Observation.total != stmt.excluded.total)
            | (Observation.anomaly != stmt.excluded.anomaly),
        ).returning(Observation.id)
        changed = len(session.execute(stmt).all())  # insérées + mises à jour

    count_after = session.scalar(
        select(func.count()).select_from(Observation).where(Observation.index_id == index.id)
    )
    run.rows_inserted = count_after - count_before
    run.rows_updated = changed - run.rows_inserted

    session.commit()
    return run

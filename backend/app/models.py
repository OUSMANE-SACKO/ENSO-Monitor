"""Modèle de domaine : Indice, Source, Import, Observation.

    Indice (ONI) 1 ──── * Observation
    Source (NOAA) 1 ─── * Import 1 ──── * Observation

- Un Indice possède plusieurs observations (une par mois).
- Une Source (URL + version NOAA) peut être importée plusieurs fois : un Import par exécution.
- Chaque Observation garde l'Import qui l'a créée -> traçabilité jusqu'au fichier NOAA.
"""
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ClimateIndex(Base):
    """Un indice climatique, ex. ONI."""

    __tablename__ = "climate_index"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)  # "ONI"
    name: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(16))  # "°C"
    description: Mapped[str | None] = mapped_column(String(1000))

    observations: Mapped[list["Observation"]] = relationship(back_populates="index")


class Source(Base):
    """D'où viennent les données : organisme, URL exacte, version."""

    __tablename__ = "source"
    __table_args__ = (UniqueConstraint("url", "version", name="uq_source_url_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(100))  # "NOAA CPC"
    url: Mapped[str] = mapped_column(String(500))
    version: Mapped[str] = mapped_column(String(50))  # ex. "ERSST v5"

    imports: Mapped[list["Import"]] = relationship(back_populates="source")


class Import(Base):
    """Une exécution de l'ETL : quand, quel fichier, combien de lignes."""

    __tablename__ = "import_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    file_sha256: Mapped[str] = mapped_column(String(64))
    rows_read: Mapped[int] = mapped_column(Integer, default=0)
    rows_inserted: Mapped[int] = mapped_column(Integer, default=0)
    rows_updated: Mapped[int] = mapped_column(Integer, default=0)  # valeurs révisées par NOAA
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0)

    source: Mapped[Source] = relationship(back_populates="imports")
    observations: Mapped[list["Observation"]] = relationship(back_populates="import_run")


class Observation(Base):
    """Une valeur mensuelle de l'indice.

    ONI = moyenne glissante sur 3 mois. On stocke la saison NOAA (ex. "DJF")
    et le mois central (DJF 1998 -> 1998-01-01) pour pouvoir filtrer par date.
    """

    __tablename__ = "observation"
    __table_args__ = (
        # Anti-doublon au niveau de la base : une seule valeur par indice et par mois.
        UniqueConstraint("index_id", "period", name="uq_observation_index_period"),
        CheckConstraint("extract(day from period) = 1", name="ck_period_first_of_month"),
        CheckConstraint("anomaly BETWEEN -10 AND 10", name="ck_anomaly_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    index_id: Mapped[int] = mapped_column(ForeignKey("climate_index.id"))
    import_id: Mapped[int] = mapped_column(ForeignKey("import_run.id"))
    period: Mapped[date] = mapped_column(Date, index=True)  # mois central, 1er du mois
    season: Mapped[str] = mapped_column(String(3))  # "DJF", "JFM", ...
    total: Mapped[float] = mapped_column(Numeric(5, 2))  # température moyenne (°C)
    anomaly: Mapped[float] = mapped_column(Numeric(4, 2))  # écart à la normale (°C)

    index: Mapped[ClimateIndex] = relationship(back_populates="observations")
    import_run: Mapped[Import] = relationship(back_populates="observations")

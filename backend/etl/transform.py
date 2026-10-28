"""Transformation du fichier NOAA ONI en lignes propres.

Fichier source : https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
Format (colonnes séparées par des espaces) :

    SEAS  YR   TOTAL  ANOM
     DJF 1950  24.72 -1.53
     JFM 1950  25.17 -1.34

- SEAS  : saison glissante de 3 mois (DJF = déc-janv-fév)
- YR    : année du mois central
- TOTAL : température moyenne de surface de la mer, région Niño 3.4 (°C)
- ANOM  : anomalie = écart à la normale (°C). C'est la valeur de l'ONI.

Ce module est PUR : pas de réseau, pas de base de données.
C'est ce qui le rend facile à tester (tests/test_transform.py).
"""
from dataclasses import dataclass
from io import StringIO

import numpy as np
import pandas as pd

# Saison -> mois central. DJF est centré sur janvier, NDJ sur décembre.
SEASON_TO_MONTH = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
    "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}

EXPECTED_COLUMNS = ["SEAS", "YR", "TOTAL", "ANOM"]


@dataclass
class TransformResult:
    clean: pd.DataFrame  # colonnes : period, season, total, anomaly
    rows_read: int
    rejected: pd.DataFrame  # lignes écartées + raison (colonne "reason")


def parse_oni(text: str) -> TransformResult:
    """Lit le texte NOAA, valide chaque ligne, retire les doublons."""
    raw = pd.read_csv(StringIO(text), sep=r"\s+", dtype=str)

    if list(raw.columns) != EXPECTED_COLUMNS:
        raise ValueError(f"Format NOAA inattendu : colonnes {list(raw.columns)}, attendu {EXPECTED_COLUMNS}")

    rows_read = len(raw)
    df = raw.copy()
    df["reason"] = ""

    # 1. Saison connue ?
    df["SEAS"] = df["SEAS"].str.strip().str.upper()
    df["month"] = df["SEAS"].map(SEASON_TO_MONTH)
    df.loc[df["month"].isna(), "reason"] = "saison inconnue"

    # 2. Année et valeurs numériques ? (errors="coerce" -> NaN si illisible)
    df["year"] = pd.to_numeric(df["YR"], errors="coerce")
    df["total"] = pd.to_numeric(df["TOTAL"], errors="coerce")
    df["anomaly"] = pd.to_numeric(df["ANOM"], errors="coerce")

    bad_year = df["year"].isna() | (df["year"] < 1850) | (df["year"] > 2100) | (df["year"] % 1 != 0)
    df.loc[(df["reason"] == "") & bad_year, "reason"] = "année invalide"

    # NOAA utilise parfois -99.9 / -99.99 comme valeur manquante.
    missing = df["anomaly"].isna() | df["total"].isna() | np.isclose(df["anomaly"], -99.9) | (df["anomaly"] <= -99)
    df.loc[(df["reason"] == "") & missing, "reason"] = "valeur manquante ou illisible"

    out_of_range = df["anomaly"].abs() > 10
    df.loc[(df["reason"] == "") & out_of_range, "reason"] = "anomalie hors plage plausible"

    rejected = df[df["reason"] != ""]
    valid = df[df["reason"] == ""].copy()

    # 3. Date du mois central (1er du mois).
    valid["period"] = pd.to_datetime(
        {"year": valid["year"].astype(int), "month": valid["month"].astype(int), "day": 1}
    ).dt.date

    # 4. Doublons : même mois présent deux fois -> on garde la DERNIÈRE occurrence
    #    (dans un fichier NOAA, la dernière ligne est la plus récente).
    dup_mask = valid.duplicated(subset="period", keep="last")
    duplicates = valid[dup_mask].assign(reason="doublon (même mois)")
    valid = valid[~dup_mask]

    clean = (
        valid.rename(columns={"SEAS": "season"})[["period", "season", "total", "anomaly"]]
        .sort_values("period")
        .reset_index(drop=True)
    )
    clean["total"] = clean["total"].round(2)
    clean["anomaly"] = clean["anomaly"].round(2)

    return TransformResult(
        clean=clean,
        rows_read=rows_read,
        rejected=pd.concat([rejected, duplicates])[["SEAS", "YR", "TOTAL", "ANOM", "reason"]],
    )

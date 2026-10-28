"""Test de données (exigé par le sujet) : transformation des observations NOAA."""
from datetime import date

import pytest

from etl.transform import parse_oni


def test_lignes_valides_conservees_et_datees(oni_sample_text):
    result = parse_oni(oni_sample_text)

    assert result.rows_read == 7
    assert list(result.clean["period"]) == [date(2000, 1, 1), date(2000, 2, 1), date(2000, 3, 1)]
    # DJF 2000 -> mois central = janvier 2000
    first = result.clean.iloc[0]
    assert first["season"] == "DJF"
    assert first["anomaly"] == -1.7


def test_doublon_retire(oni_sample_text):
    result = parse_oni(oni_sample_text)
    assert (result.clean["period"] == date(2000, 3, 1)).sum() == 1
    assert "doublon (même mois)" in set(result.rejected["reason"])


def test_lignes_invalides_rejetees_avec_raison(oni_sample_text):
    reasons = set(parse_oni(oni_sample_text).rejected["reason"])
    assert {"saison inconnue", "année invalide", "valeur manquante ou illisible"} <= reasons


def test_format_inattendu_refuse():
    with pytest.raises(ValueError, match="Format NOAA inattendu"):
        parse_oni("A B C\n1 2 3\n")

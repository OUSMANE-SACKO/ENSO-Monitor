from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def oni_sample_text() -> str:
    # Données de TEST au format NOAA : valeurs inventées pour piloter les cas
    # (doublon, saison inconnue, année illisible, valeur manquante).
    # Ce ne sont PAS des mesures réelles.
    return (FIXTURES / "oni_sample.txt").read_text()
